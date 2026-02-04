import streamlit as st
import os
import fnmatch
import re
import pandas as pd
import matplotlib.pyplot as plt

# Set page to wide mode for better plotting
st.set_page_config(layout="wide")

def parse_dimensions_from_path(rel_dir_path):
    dims = {}
    parts = rel_dir_path.split(os.sep)
    pattern = re.compile(r'^([A-Za-z0-9]+?)(_?)(\d+)$')  

    for part in parts:
        if part == '.': continue
        match = pattern.match(part)
        if match:
            name = match.group(1)
            value = int(match.group(3))
            dims[name] = value
    return dims

@st.cache_data
def load_data(root_dir, csv_file_pattern):
    data_records = []
    
    if not os.path.exists(root_dir):
        return pd.DataFrame(), f"Root directory '{root_dir}' not found."

    # Walk through the directory
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter files matching the pattern
        for filename in fnmatch.filter(filenames, csv_file_pattern):
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(dirpath, root_dir)
            dims = parse_dimensions_from_path(rel_path)
            
            try:
                # Read CSV
                df_file = pd.read_csv(full_path)
                df_file.columns = df_file.columns.str.strip()
                
                # We need to flatten the CSV data into records
                # But our logic assumes 'y' is a column we can pick later.
                # So we must read ALL columns of interest? 
                # To be efficient, let's just read the structure first.
                # Actually, the previous script aggregated immediately based on a chosen Y.
                # In Streamlit, we want to choose Y dynamically.
                # So we should store the scalar values for all potential columns.
                
                # Get numeric columns only
                numeric_cols = df_file.select_dtypes(include=['number']).columns
                
                # Create a record that has dimensions + mean of every numeric column
                record = dims.copy()
                for col in numeric_cols:
                     record[col] = df_file[col].mean()
                
                record['source_file'] = full_path
                data_records.append(record)
                
            except Exception as e:
                continue
            
    if not data_records:
        return pd.DataFrame(), "No matching CSV files found."
        
    return pd.DataFrame(data_records), None

def main():
    st.title("CSV Analysis Dashboard")
    
    # --- Sidebar Configuration ---
    st.sidebar.header("Data Loading")
    
    # Defaults
    default_root = "Experimants/flexicas/experiment-1"
    default_csv = "terminatedl1d_set_utilization_BL*.csv"
    
    root_dir = st.sidebar.text_input("Root Directory", value=default_root)
    csv_pattern = st.sidebar.text_input("CSV Pattern", value=default_csv)
    
    if st.sidebar.button("Reload Data"):
        st.cache_data.clear()
        
    # Load Data
    with st.spinner("Loading data..."):
        df_raw, error = load_data(root_dir, csv_pattern)
        
    if not df_raw.empty:
        st.success(f"Loaded {len(df_raw)} records.")
    else:
        if error:
            st.error(error)
        return

    st.sidebar.markdown("---")
    st.sidebar.header("Plot Configuration")

    # Detect Dimensions vs Data columns
    # Heuristic: Dimensions are from paths (usually disjoint from CSV cols, but not always)
    # In 'load_data', we merged them.
    # We can separate them if we know which keys came from directory parsing. 
    # But for now, let's just let user pick from all columns.
    
    all_cols = list(df_raw.columns)
    if 'source_file' in all_cols: all_cols.remove('source_file')
    
    # 1. Select Axes
    x_dim = st.sidebar.selectbox("X Axis (Dimension)", options=all_cols, index=0)
    y_col = st.sidebar.selectbox("Y Axis (Value)", options=all_cols, index=len(all_cols)-1 if len(all_cols)>1 else 0)
    
    # 2. Select Neglected Dims (Average over)
    # Default nothing
    neglect_dims = st.sidebar.multiselect("Neglect Dimensions (Average Over)", options=[c for c in all_cols if c not in [x_dim, y_col]])
    
    # 3. Aggregation
    df_agg = df_raw.copy()
    if neglect_dims:
        # dims to keep = all - neglect - numerical_values
        # But we want to keep specific numerical value 'y_col'.
        # Actually easier: Group By (All Cols - Neglect - Other Numeric Cols)
        # But 'Other Numeric Cols' are many.
        
        # Strategy:
        # 1. Identify "Grouping Dimensions": Everything that is NOT a metric and NOT in neglect.
        # But we don't know which are metrics vs path dimensions easily.
        # Let's assume the user selects neglect dims correctly.
        # We also need to average Y.
        
        # Simpler: Drop neglect cols, then group by everything else?
        # No, that groups by y_values too.
        
        # Let's identify "Potential Dimensions" -> columns with low cardinality?
        # Or better: User filters remaining dims via sliders. 
        # So "neglect" just means "remove this column and avg duplicates".
        
        # Drop neglect columns
        # Drop OTHER y columns (we only care about current y_col for averaging)
        cols_to_keep = [x_dim, y_col] + [c for c in all_cols if c not in neglect_dims and c != x_dim and c != y_col]
        
        # To average properly, we must only keep the relevant columns
        df_subset = df_agg[cols_to_keep]
        
        # Group by everything except y_col
        group_cols = [c for c in cols_to_keep if c != y_col]
        df_agg = df_subset.groupby(group_cols, as_index=False)[y_col].mean()

    # 4. Subplots Selection
    remaining_cols = [c for c in df_agg.columns if c not in [x_dim, y_col]]
    
    x_subplot = st.sidebar.selectbox("Subplot Columns (Dim)", options=["None"] + remaining_cols, index=0)
    if x_subplot == "None": x_subplot = None
    
    remaining_cols_2 = [c for c in remaining_cols if c != x_subplot]
    y_subplot = st.sidebar.selectbox("Subplot Rows (Dim)", options=["None"] + remaining_cols_2, index=0)
    if y_subplot == "None": y_subplot = None

    # 5. Sliders for Rest
    # Dims that act as filters
    filter_dims = [c for c in df_agg.columns if c not in [x_dim, y_col, x_subplot, y_subplot] and c != 'source_file']
    filter_dims.sort()
    
    st.sidebar.markdown("### Filters")
    filters = {}
    for dim in filter_dims:
        vals = sorted(df_agg[dim].unique())
        if len(vals) > 1:
            # Use a select_slider regarding actual values (better than int slider)
            val = st.sidebar.select_slider(f"{dim}", options=vals, value=vals[0])
            filters[dim] = val
        else:
            filters[dim] = vals[0]
            
    # --- Main Plotting Area ---
    
    # Filter Data
    df_plot = df_agg.copy()
    for dim, val in filters.items():
        df_plot = df_plot[df_plot[dim] == val]
        
    if df_plot.empty:
        st.warning("No data for this filter configuration.")
        return
        
    # Generate Grid
    row_vals = [None]
    col_vals = [None]
    if y_subplot: row_vals = sorted(df_plot[y_subplot].unique())
    if x_subplot: col_vals = sorted(df_plot[x_subplot].unique())
    
    nrows = len(row_vals)
    ncols = len(col_vals)
    
    fig_height = 4 * nrows
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10, fig_height), squeeze=False, sharex=True, sharey=True)
    
    for i, r_val in enumerate(row_vals):
        for j, c_val in enumerate(col_vals):
            ax = axes[i, j]
            
            subset = df_plot.copy()
            title_parts = []
            
            if y_subplot:
                subset = subset[subset[y_subplot] == r_val]
                title_parts.append(f"{y_subplot}={r_val}")
            
            if x_subplot:
                subset = subset[subset[x_subplot] == c_val]
                title_parts.append(f"{x_subplot}={c_val}")
            
            if not subset.empty:
                subset = subset.sort_values(by=x_dim)
                ax.plot(subset[x_dim], subset[y_col], marker='o')
                ax.grid(True)
            else:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                
            if title_parts:
                ax.set_title(", ".join(title_parts), fontsize=10)
            
            if i == nrows - 1: ax.set_xlabel(x_dim)
            if j == 0: ax.set_ylabel(y_col)

    st.pyplot(fig)

if __name__ == "__main__":
    main()

import os
import argparse
import fnmatch
import re
import pandas as pd
import matplotlib.pyplot as plt
import sys
import itertools

def parse_dimensions_from_path(rel_dir_path):
    """
    Parses dimensions from a relative directory path.
    Expected format for each directory: NameValue or Name_Value (e.g., L1_32, LW16).
    """
    dims = {}
    parts = rel_dir_path.split(os.sep)
    
    # Regex to capture Name and Value. 
    # Starts with letters, optional underscore, then digits.
    # We allow more loose matching if needed, but the prompt example suggests this structure.
    pattern = re.compile(r'^([A-Za-z0-9]+?)(_?)(\d+)$')  
    # Using [A-Za-z0-9]+ to allow alphanumeric names like "L1" in L1_32.
    # The example "L1_32" -> Name: L1, Value: 32.
    # The example "LW16" -> Name: LW, Value: 16.

    for part in parts:
        if part == '.': continue
        match = pattern.match(part)
        if match:
            name = match.group(1)
            value = int(match.group(3))
            dims[name] = value
        # else:
            # If a folder doesn't match the pattern, we ignore it as a dimension?
            # The prompt implies the structure *defines* the dimensions. 
            # We will ignore folders that don't look like dimensions (e.g. if there's an intermediate folder)
            # unless it's critical. Based on "find all the csv files... each directory structure defines the all dimensions",
            # I'll adhere to the pattern.

    return dims

def scan_and_collect_data(root_dir, csv_file_pattern, x_dim, y_col):
    data_records = []
    
    # Walk through the directory
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter files matching the pattern
        for filename in fnmatch.filter(filenames, csv_file_pattern):
            full_path = os.path.join(dirpath, filename)
            
            # Get path relative to the root to extract dimensions
            rel_path = os.path.relpath(dirpath, root_dir)
            
            # Parse dimensions
            dims = parse_dimensions_from_path(rel_path)
            
            # Read CSV
            try:
                df = pd.read_csv(full_path)
            except Exception as e:
                print(f"Error reading {full_path}: {e}", file=sys.stderr)
                continue
            
            # Check if columns exist
            # The prompt says "do not need to care about the other data in the csv."
            # "y will be the average of a data column in the csv"
            
            # The user might provide a column name that exists in changes formats.
            # We check if y_col is in the csv simply.
            
            # Handle whitespace in column names potentially?
            df.columns = df.columns.str.strip()
            
            if y_col not in df.columns:
                print(f"Column '{y_col}' not found in {full_path}. Skipping.", file=sys.stderr)
                continue
                
            # Calculate average
            y_val = df[y_col].mean()
            
            # Store record
            record = dims.copy()
            record['y_value_avg'] = y_val
            record['source_file'] = full_path # For debugging if needed
            data_records.append(record)
            
    return pd.DataFrame(data_records)

def plot_data(df, x_dim, y_dim_label, col_dim=None, row_dim=None, color_dims=None, output_dir="plots"):
    if df.empty:
        print("No data found to plot.")
        return

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Determine "File Separation Dims"
    # All dimensions that are NOT x_dim, col_dim, row_dim, 'y_value_avg', 'source_file'
    exclude_cols = {x_dim, 'y_value_avg', 'source_file'}
    if col_dim: exclude_cols.add(col_dim)
    if row_dim: exclude_cols.add(row_dim)
    
    if color_dims:
        # Check validity of color_dims
        valid_color_dims = [d for d in color_dims if d in df.columns]
        if len(valid_color_dims) != len(color_dims):
            missing = set(color_dims) - set(valid_color_dims)
            print(f"Warning: color_dims {missing} not found in data.")
        color_dims = valid_color_dims
        exclude_cols.update(color_dims)
    
    file_sep_dims = [c for c in df.columns if c not in exclude_cols]
    
    # 2. Group by file_sep_dims to run the loop for creating files
    if not file_sep_dims:
        # Only one group (one file)
        file_groups = [(("All",), df)]
        file_sep_dims = ["Dataset"] # Dummy name
    else:
        file_groups = df.groupby(file_sep_dims)

    print(f"Generating {len(file_groups) if hasattr(file_groups, '__len__') else 'multiple'} plots in '{output_dir}'...")

    for name, group_df in file_groups:
        if not isinstance(name, tuple):
            name = (name,)
            
        # Construct filename
        filename_parts = []
        file_title_parts = []
        for dim, val in zip(file_sep_dims, name):
            filename_parts.append(f"{dim}_{val}")
            file_title_parts.append(f"{dim}={val}")
            
        filename = "_".join(filename_parts) + ".png"
        file_title = ", ".join(file_title_parts)
        out_path = os.path.join(output_dir, filename)

        # 3. Setup Grid (Subplots)
        # Determine unique row values and col values
        row_vals = [None]
        col_vals = [None]
        
        if row_dim:
            row_vals = sorted(group_df[row_dim].unique())
        if col_dim:
            col_vals = sorted(group_df[col_dim].unique())
            
        nrows = len(row_vals)
        ncols = len(col_vals)
        
        # Consistent Style Map for Color Dims within this file
        unique_color_keys = []
        if color_dims:
            # Get all unique combinations present in this file's data
            # Helper to normalize keys to tuple
            def normalize_key(k):
                if isinstance(k, tuple): return k
                return (k,)

            color_groups = group_df.groupby(color_dims)
            # Use normalize_key to ensure robust comparison whether pandas returns scalars or tuples
            unique_color_keys = sorted(list(set([normalize_key(k) for k in color_groups.groups.keys()])))
        else:
            unique_color_keys = ['Data'] # Default single key

        # Create markers/colors cycle
        markers = itertools.cycle(['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'd', '|', '_'])
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_cycle = itertools.cycle(colors)

        style_map = {}
        for key in unique_color_keys:
             style_map[key] = {'marker': next(markers), 'color': next(color_cycle)}

        # Create figure with subplots
        # Adjust figsize based on grid size
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False, sharex=True, sharey=True)
        
        fig.suptitle(f"{y_dim_label} vs {x_dim}\n{file_title}", fontsize=16)

        # 4. Fill Subplots
        for i, r_val in enumerate(row_vals):
            for j, c_val in enumerate(col_vals):
                ax = axes[i, j]
                
                # Filter for this subplot
                subset = group_df.copy()
                subplot_title = []
                
                if row_dim:
                    subset = subset[subset[row_dim] == r_val]
                    subplot_title.append(f"{row_dim}={r_val}")
                if col_dim:
                    subset = subset[subset[col_dim] == c_val]
                    subplot_title.append(f"{col_dim}={c_val}")
                
                if subset.empty:
                    ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                    continue
                
                # Plotting logic
                if color_dims:
                    # Group by color dims
                    line_groups = subset.groupby(color_dims)
                    
                    for l_name, l_group in line_groups:
                        # Normalize key
                        key = normalize_key(l_name)
                        
                        style = style_map.get(key, {'marker': 'o', 'color': 'black'})
                        
                        l_label_parts = []
                        vals = key
                        for dim, val in zip(color_dims, vals):
                             l_label_parts.append(f"{dim}={val}")
                        l_label = ", ".join(l_label_parts)
                        
                        l_group = l_group.sort_values(by=x_dim)
                        ax.plot(l_group[x_dim], l_group['y_value_avg'], 
                                marker=style['marker'], color=style['color'], label=l_label)
                        
                    # Add legend to subplot
                    ax.legend(fontsize='x-small')
                else:
                    # Single line
                    subset = subset.sort_values(by=x_dim)
                    style = style_map['Data']
                    ax.plot(subset[x_dim], subset['y_value_avg'], 
                            marker=style['marker'], color=style['color'], label='Data')

                ax.set_title(", ".join(subplot_title))
                ax.grid(True)
                
                # Label axis only on edges
                if i == nrows - 1:
                    ax.set_xlabel(x_dim)
                if j == 0:
                    ax.set_ylabel(y_dim_label)

        plt.tight_layout()
        plt.subplots_adjust(top=0.90) # Make room for suptitle
        plt.savefig(out_path)
        plt.close(fig) # Close to free memory
        print(f"Saved {out_path}")
    
def get_available_params(root_dir, csv_file_pattern):
    """Scans for the first matching CSV to determine available dimensions and columns."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, csv_file_pattern):
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(dirpath, root_dir)
            
            # Get dimensions
            dims = parse_dimensions_from_path(rel_path)
            
            # Get columns
            try:
                # Read just the header
                df = pd.read_csv(full_path, nrows=0) 
                columns = df.columns.str.strip().tolist()
                return list(dims.keys()), columns
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                continue # Try next file if this one is bad
    return [], []

def main():
    parser = argparse.ArgumentParser(description="CSV Analysis and Plotting Tool")
    parser.add_argument("--csv_file", required=True, help="Pattern for CSV file name (e.g., data_*.csv)")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--x", help="Dimension to use for X axis")
    parser.add_argument("--y", help="CSV Column to average for Y axis")
    parser.add_argument("--list_params", action="store_true", help="List available X dimensions and Y columns found in the data")
    parser.add_argument("--neglect_dims", nargs='+', help="List of dimensions to ignore (data will be averaged over these dimensions)")
    parser.add_argument("--x_subplot", help="Dimension to use for subplot columns")
    parser.add_argument("--y_subplot", help="Dimension to use for subplot rows")
    parser.add_argument("--color_dims", nargs='+', help="List of dimensions to differentiate by color/marker within subplots")
    parser.add_argument("--output_dir", default="plots", help="Directory to save output plots")
    
    args = parser.parse_args()

    if args.list_params:
        print(f"Scanning {args.root} for parameters in files matching '{args.csv_file}'...")
        dims, cols = get_available_params(args.root, args.csv_file)
        if not dims and not cols:
             print("No matching files found to extract parameters.")
        else:
            print("\nAvailable Dimensions (Candidates for --x):")
            for d in dims:
                print(f"  {d}")
            print("\nAvailable CSV Columns (Candidates for --y):")
            for c in cols:
                print(f"  {c}")
        return

    if not args.x or not args.y:
        parser.error("the following arguments are required: --x, --y (unless --list_params is used)")
    
    print(f"Scanning {args.root} for {args.csv_file}...")
    df = scan_and_collect_data(args.root, args.csv_file, args.x, args.y)
    
    print(f"Collected {len(df)} data points.")
    if not df.empty:
        # Check if x_dim is in columns
        if args.x not in df.columns:
             print(f"Error: X dimension '{args.x}' not found in the directory structure.")
             print("Found dimensions:", [c for c in df.columns if c not in ['y_value_avg', 'source_file']])
             return

        if args.neglect_dims:
            # Validate that we aren't neglecting the X dimension
            if args.x in args.neglect_dims:
                 print(f"Warning: X dimension '{args.x}' is in neglect list. Removing it from neglect list to preserve X-axis.")
                 args.neglect_dims = [d for d in args.neglect_dims if d != args.x]

            print(f"Neglecting dimensions: {args.neglect_dims}")
            
            # Filter to only dimensions that are actually in the dataframe
            dims_to_drop = [d for d in args.neglect_dims if d in df.columns]
            
            if dims_to_drop:
                # We must drop 'source_file' before grouping as it is unique per row
                if 'source_file' in df.columns:
                    df = df.drop(columns=['source_file'])
                
                # Group by all remaining columns (including X) and average
                # Remaining columns = All columns - dims_to_drop - y_value_avg
                group_cols = [c for c in df.columns if c not in dims_to_drop and c != 'y_value_avg']
                
                if group_cols:
                    # Group and mean
                    df = df.groupby(group_cols, as_index=False)['y_value_avg'].mean()
                    print(f"Data aggregated over neglected dimensions. New data points: {len(df)}")
        
        print("Generating plot...")
        plot_data(df, args.x, args.y, col_dim=args.x_subplot, row_dim=args.y_subplot, color_dims=args.color_dims, output_dir=args.output_dir)
    else:
        print("No matching data found.")

if __name__ == "__main__":
    main()

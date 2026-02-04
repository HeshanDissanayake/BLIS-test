import os
import argparse
import fnmatch
import re
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import itertools

def parse_dimensions_from_path(rel_dir_path):
    """
    Parses dimensions from a relative directory path.
    Expected format for each directory: NameValue or Name_Value (e.g., L1_32, LW16).
    """
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

def scan_and_collect_data(root_dir, csv_file_pattern, x_dim, y_col, z_dim):
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
            
            # Handle whitespace in column names
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

def plot_data_3d(df, x_dim, z_dim, y_dim_label, col_dim=None, row_dim=None, color_dims=None, output_dir="plots_3d"):
    if df.empty:
        print("No data found to plot.")
        return

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Validate dimensions
    if x_dim not in df.columns:
         print(f"Dimension '{x_dim}' not found in collected data.")
         return
    if z_dim not in df.columns:
         print(f"Dimension '{z_dim}' not found in collected data.")
         return

    # 1. Determine "File Separation Dims"
    # All dimensions that are NOT x_dim, z_dim, col_dim, row_dim, 'y_value_avg', 'source_file'
    exclude_cols = {x_dim, z_dim, 'y_value_avg', 'source_file'}
    if col_dim: exclude_cols.add(col_dim)
    if row_dim: exclude_cols.add(row_dim)
    
    if color_dims:
        valid_color_dims = [d for d in color_dims if d in df.columns]
        color_dims = valid_color_dims
        exclude_cols.update(color_dims)
    
    file_sep_dims = [c for c in df.columns if c not in exclude_cols]
    
    # 2. Group by file_sep_dims to run the loop for creating files
    if not file_sep_dims:
        file_groups = [(("All",), df)]
        file_sep_dims = ["Dataset"] 
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
            def normalize_key(k):
                if isinstance(k, tuple): return k
                return (k,)

            color_groups = group_df.groupby(color_dims)
            unique_color_keys = sorted(list(set([normalize_key(k) for k in color_groups.groups.keys()])))
        else:
            unique_color_keys = ['Data'] 

        markers = itertools.cycle(['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'd', '|', '_'])
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_cycle = itertools.cycle(colors)

        style_map = {}
        for key in unique_color_keys:
             style_map[key] = {'marker': next(markers), 'color': next(color_cycle)}

        # Create figure with 3D subplots
        fig = plt.figure(figsize=(6 * ncols, 5 * nrows))
        fig.suptitle(f"{y_dim_label} (avg) vs {x_dim} vs {z_dim}\n{file_title}", fontsize=16)

        # 4. Fill Subplots
        for i, r_val in enumerate(row_vals):
            for j, c_val in enumerate(col_vals):
                # Calculate subplot index (1-based)
                index = i * ncols + j + 1
                ax = fig.add_subplot(nrows, ncols, index, projection='3d')
                
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
                    ax.text2D(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
                    continue
                
                # Plotting logic
                if color_dims:
                    line_groups = subset.groupby(color_dims)
                    
                    for l_name, l_group in line_groups:
                        # Normalize key
                        def normalize_key_local(k): 
                            if isinstance(k, tuple): return k
                            return (k,)
                        key = normalize_key_local(l_name)
                        
                        style = style_map.get(key, {'marker': 'o', 'color': 'black'})
                        
                        l_label_parts = []
                        vals = key
                        for dim, val in zip(color_dims, vals):
                             l_label_parts.append(f"{dim}={val}")
                        l_label = ", ".join(l_label_parts)
                        
                        # Sort for line continuity roughly (by X then Z or vice versa)
                        # For 3D lines, it can be tricky. Often scatter is safer or wireframe if grid.
                        # We will try line plot by sorting by X.
                        l_group = l_group.sort_values(by=x_dim)
                        
                        ax.plot(l_group[x_dim], l_group[z_dim], l_group['y_value_avg'], 
                                marker=style['marker'], color=style['color'], label=l_label)
                        
                    ax.legend(fontsize='x-small')
                else:
                    subset = subset.sort_values(by=x_dim)
                    style = style_map['Data']
                    ax.plot(subset[x_dim], subset[z_dim], subset['y_value_avg'], 
                            marker=style['marker'], color=style['color'], label='Data')

                ax.set_title(", ".join(subplot_title))
                ax.set_xlabel(x_dim)
                ax.set_ylabel(z_dim)
                ax.set_zlabel(y_dim_label)

        plt.tight_layout()
        plt.subplots_adjust(top=0.90)
        plt.savefig(out_path)
        plt.close(fig)
        print(f"Saved {out_path}")

def get_available_params(root_dir, csv_file_pattern):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, csv_file_pattern):
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(dirpath, root_dir)
            dims = parse_dimensions_from_path(rel_path)
            try:
                df = pd.read_csv(full_path, nrows=0) 
                columns = df.columns.str.strip().tolist()
                return list(dims.keys()), columns
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                continue 
    return [], []

def main():
    parser = argparse.ArgumentParser(description="3D CSV Analysis and Plotting Tool")
    parser.add_argument("--csv_file", required=True, help="Pattern for CSV file name (e.g., data_*.csv)")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--x", help="Dimension to use for X axis")
    parser.add_argument("--z", help="Dimension to use for Z axis (the 3rd dimension)")
    parser.add_argument("--y", help="CSV Column to average for Y axis (Vertical axis in 3D plot usually)")
    parser.add_argument("--list_params", action="store_true", help="List available dimensions and columns")
    parser.add_argument("--neglect_dims", nargs='+', help="List of dimensions to ignore (average over)")
    parser.add_argument("--x_subplot", help="Dimension to use for subplot columns")
    parser.add_argument("--y_subplot", help="Dimension to use for subplot rows")
    parser.add_argument("--color_dims", nargs='+', help="List of dimensions to differentiate by color/marker within subplots")
    parser.add_argument("--output_dir", default="plots_3d", help="Directory to save output plots")
    
    args = parser.parse_args()

    if args.list_params:
        print(f"Scanning {args.root} for parameters in files matching '{args.csv_file}'...")
        dims, cols = get_available_params(args.root, args.csv_file)
        if not dims and not cols:
             print("No matching files found to extract parameters.")
        else:
            print("\nAvailable Dimensions (Candidates for --x, --z):")
            for d in dims:
                print(f"  {d}")
            print("\nAvailable CSV Columns (Candidates for --y):")
            for c in cols:
                print(f"  {c}")
        return

    if not args.x or not args.y or not args.z:
        parser.error("the following arguments are required: --x, --y, --z (unless --list_params is used)")
    
    print(f"Scanning {args.root} for {args.csv_file}...")
    df = scan_and_collect_data(args.root, args.csv_file, args.x, args.y, args.z)
    
    print(f"Collected {len(df)} data points.")
    if not df.empty:
        # Check if x_dim/z_dim is in columns is partially done inside plot_data_3d, but checking neglect conflict here too
        if args.neglect_dims:
            for vital_dim in [args.x, args.z]:
                if vital_dim in args.neglect_dims:
                    print(f"Warning: Dimension '{vital_dim}' is in neglect list. Removing it to preserve axis.")
                    args.neglect_dims = [d for d in args.neglect_dims if d != vital_dim]

            print(f"Neglecting dimensions: {args.neglect_dims}")
            
            dims_to_drop = [d for d in args.neglect_dims if d in df.columns]
            
            if dims_to_drop:
                if 'source_file' in df.columns:
                    df = df.drop(columns=['source_file'])
                
                group_cols = [c for c in df.columns if c not in dims_to_drop and c != 'y_value_avg']
                
                if group_cols:
                    df = df.groupby(group_cols, as_index=False)['y_value_avg'].mean()
                    print(f"Data aggregated over neglected dimensions. New data points: {len(df)}")
        
        print("Generating 3D plot...")
        plot_data_3d(df, args.x, args.z, args.y, col_dim=args.x_subplot, row_dim=args.y_subplot, color_dims=args.color_dims, output_dir=args.output_dir)
    else:
        print("No matching data found.")

if __name__ == "__main__":
    main()

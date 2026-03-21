#!/usr/bin/env python3
import os
import re
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import sys
import numpy as np
from itertools import cycle

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze and plot experimental data from a hierarchical directory structure.")
    
    # Input/Data arguments
    parser.add_argument("--root", required=True, help="Base directory to scan.")
    parser.add_argument("--x", help="Dimension name to map to the X-axis.")
    parser.add_argument("--y", nargs='+', help="Value(s) from the json to map to the Y-axis (supports dot notation e.g., 'stats.miss_rate').")
    
    # Plotting layout arguments
    parser.add_argument("--x_subplot", help="Dimension to map to subplot columns.")
    parser.add_argument("--y_subplot", help="Dimension to map to subplot rows.")
    parser.add_argument("--color_dims", nargs='*', default=[], help="List of dimensions to differentiate lines/markers within a single plot.")
    
    # Data processing arguments
    parser.add_argument("--neglect_dims", nargs='*', default=[], help="List of dimensions to ignore; data will be averaged across these dimensions.")
    parser.add_argument("--list_params", action="store_true", help="Scan directory and json to list all available dimensions and exit.")
    
    # Output
    parser.add_argument("--output_dir", default="plots", help="Directory to save output plots (default: 'plots').")
    parser.add_argument("--preview", action="store_true", help="Show the first plot in a window.")
    parser.add_argument("--global_scale", action="store_true", help="Use the same Y-axis scale for all plots based on global min/max.")
    parser.add_argument("--x_ticks_from_data", action="store_true", help="Set X-axis ticks to match data points exactly.")
    parser.add_argument("--y_label", help="Custom label for the Y-axis. Defaults to the metric name(s).")
    parser.add_argument("--secondary_x_formula", help="Formula to compute secondary X-axis values from primary X values. Use 'x' as the variable (e.g., 'x*x*2').")
    parser.add_argument("--secondary_x_label", default="Secondary X", help="Label for the secondary X-axis (default: 'Secondary X').")
    parser.add_argument("--dump_csv", help="If set, dump the collected data as a CSV file to this path. X values become rows, Y metrics become columns.")
    parser.add_argument("--value", help="JSON metric for 2D pivot CSV: --x = rows, --y = columns, --value = cell values. Requires --dump_csv.")
    parser.add_argument("--label", help="Prefix for pivot CSV column names. E.g. --label misses → columns named misses_4, misses_8, etc.")
    
    return parser.parse_args()

def parse_folder_name(folder_name):
    """
    Parses folder names to extract key-value pairs.
    Supported patterns:
    1. Name_Value (e.g., L1_32, Associativity_4, Experiment_1)
    2. NameValue (e.g., LW16, MC4096) - where Value is numeric
    """
    # Pattern 1: Name_Value (Name can contain alphanumeric, Value can be anything, but we usually look for numbers/strings)
    # We look for the last underscore to handle names like "My_Param_12" -> "My_Param": 12 ?
    # Or just greedy underscore? prompt example: L1_32. 
    # Let's try matching trailing value first.
    
    # Case: Name_Value Where Value is potentially numeric or string
    # We assume 'Name' does not end with a digit if 'Value' starts with a digit in the NameValue case.
    
    # Regex for Name_Value
    match_underscore = re.match(r"^([a-zA-Z0-9_]+)_([a-zA-Z0-9\.]+)$", folder_name)
    if match_underscore:
        return match_underscore.group(1), match_underscore.group(2)
    
    # Regex for NameValue (strictly letters followed by numbers)
    match_concat = re.match(r"^([a-zA-Z]+)(\d+(?:\.\d+)?)$", folder_name)
    if match_concat:
        return match_concat.group(1), match_concat.group(2)
        
    return None, None

def get_json_value(data, key_path):
    """Retrieve a value from a nested dictionary using dot notation."""
    keys = key_path.split('.')
    val = data
    try:
        for k in keys:
            val = val[k]
        return val
    except (KeyError, TypeError):
        return None

def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], name + a + '.')
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

def collect_data(root_dir, target_y_key=None, list_mode=False):
    data_records = []
    
    if not os.path.exists(root_dir):
        print(f"Error: Root directory '{root_dir}' does not exist.")
        sys.exit(1)

    print(f"Scanning directory: {root_dir}...")
    
    # Walk directory
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Find JSON files
        json_files = [f for f in filenames if f.endswith('.json')]
        
        for j_file in json_files:
            file_path = os.path.join(dirpath, j_file)
            
            # Parse parameters from directory path relative to root
            rel_path = os.path.relpath(dirpath, root_dir)
            path_parts = rel_path.split(os.sep)
            
            record = {}
            for part in path_parts:
                if part == '.': continue
                k, v = parse_folder_name(part)
                if k:
                    # Try converting value to number
                    try:
                        if '.' in v:
                            v = float(v)
                        else:
                            v = int(v)
                    except (ValueError, TypeError):
                        pass # keep as string
                    record[k] = v
            
            # Read JSON content
            try:
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                
                if list_mode:
                    # Return immediately with found keys
                    flattened = flatten_json(json_data)
                    return list(record.keys()), list(flattened.keys())

                if target_y_key:
                    # Support single key or list of keys
                    keys = target_y_key if isinstance(target_y_key, list) else [target_y_key]
                    for key in keys:
                        val = get_json_value(json_data, key)
                        if val is not None:
                            record[key] = val
                        else:
                            record[key] = np.nan
                
                data_records.append(record)

            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                
    return data_records

def get_scale_factor(series):
    """Calculates a scale factor (power of 10) to normalize data."""
    max_val = series.abs().max()
    if max_val == 0 or pd.isna(max_val):
        return 1.0, 0
    
    # log10(max_val) e.g. 3000 -> 3.47 -> floor 3 -> 10^3
    exponent = int(np.floor(np.log10(max_val)))
    factor = 10**exponent
    return factor, exponent

def main():
    args = parse_args()

    # --- Mode: List Parameters ---
    if args.list_params:
        path_dims, json_dims = collect_data(args.root, list_mode=True)
        if path_dims is None: # No data found
            print("No JSON files or parseable directories found.")
        else:
            print("\nAvailable Directory Dimensions (Parameters):")
            for d in sorted(list(set(path_dims))):
                 print(f"  - {d}")
            print("\nAvailable JSON Keys (Metrics):")
            for d in sorted(json_dims):
                print(f"  - {d}")
        return

    # --- Validation ---
    if not args.x:
        print("Error: Argument --x is required (unless using --list_params).")
        sys.exit(1)
    if not args.y:
        print("Error: Argument --y is required (unless using --list_params).")
        sys.exit(1)

    # --- 2D Pivot CSV mode (--value given) ---
    # In this mode: --x = row dim, --y = col dim (both directory dims), --value = JSON metric
    if args.value:
        if not args.dump_csv:
            print("Error: --value requires --dump_csv to specify the output path.")
            sys.exit(1)
        y_dim = args.y[0] if isinstance(args.y, list) else args.y
        raw = collect_data(args.root, target_y_key=args.value)
        if not raw:
            print("No data found.")
            sys.exit(1)
        pv_df = pd.DataFrame(raw)
        pv_df[args.value] = pd.to_numeric(pv_df[args.value], errors='coerce')
        pivot = pv_df.pivot_table(index=args.x, columns=y_dim, values=args.value, aggfunc='mean')
        # Reindex so all combinations appear (empty → NaN)
        all_x = sorted(pv_df[args.x].dropna().unique())
        all_y = sorted(pv_df[y_dim].dropna().unique())
        pivot = pivot.reindex(index=all_x, columns=all_y)
        pivot.index.name = args.x
        pivot.columns.name = y_dim
        if args.label:
            pivot.columns = [f"{args.label}_{int(c) if float(c).is_integer() else c}" for c in pivot.columns]
            pivot.columns.name = None
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_csv)), exist_ok=True)
        pivot.to_csv(args.dump_csv)
        print(f"Pivot CSV ({args.x} x {y_dim}) dumped to: {args.dump_csv}")
        return

    # --- Data Collection ---
    # Convert args.y to list if not already (it should be list due to nargs='+')
    y_cols = args.y if isinstance(args.y, list) else [args.y]

    data = collect_data(args.root, target_y_key=y_cols)
    if not data:
        print("No data found matching requirements.")
        sys.exit(1)
        
    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} records.")
    
    # Ensure numerical consistency for X and Y if possible
    # Loop over all y columns
    for y_col in y_cols:
        try:
            df[y_col] = pd.to_numeric(df[y_col])
        except:
            print(f"Warning: Y-axis column '{y_col}' contains non-numeric data.")

    # --- Data Processing: Neglect Dimensions ---
    # Determine which columns are "dimensions" (exclude Y metric)
    all_cols = set(df.columns)
    dims = all_cols - set(y_cols)
    
    if args.neglect_dims:
        print(f"Neglecting dimensions (averaging): {args.neglect_dims}")
        # Valid dimensions to group by = All dims - Neglected dims
        # Ensure we don't lose the structural dims needed for plotting
        group_dims = [c for c in dims if c not in args.neglect_dims]
        
        if not group_dims:
            print("Error: neglecting all dimensions leaves nothing to group by!")
            sys.exit(1)
            
        # Group and Average
        # We only aggregate the Y columns. Other columns (dimensions) become the index.
        df = df.groupby(group_dims)[y_cols].mean().reset_index()

    # --- CSV Dump ---
    if args.dump_csv:
        # Pivot: x as rows, each y metric (optionally combined with other dims) as columns
        other_dims = [c for c in df.columns if c not in y_cols and c != args.x]
        if other_dims:
            # Multi-column: combine other dims + metric name as column label
            records = []
            for _, row in df.iterrows():
                rec = {args.x: row[args.x]}
                suffix = "_".join(str(row[d]) for d in other_dims)
                for y_col in y_cols:
                    rec[f"{y_col}[{suffix}]"] = row[y_col]
                records.append(rec)
            csv_df = pd.DataFrame(records)
        else:
            csv_df = df[[args.x] + y_cols].copy()
        csv_df = csv_df.set_index(args.x).sort_index()
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_csv)), exist_ok=True)
        csv_df.to_csv(args.dump_csv)
        print(f"CSV dumped to: {args.dump_csv}")

    # --- Data Scaling & Melting ---
    # We want to normalize each Y column and melt them into a single column for plotting
    scaled_y_cols = []
    
    for y_col in y_cols:
        factor, exponent = get_scale_factor(df[y_col])
        
        # Format label: "Metric (x10^E)" or just "Metric" if E=0
        if exponent != 0:
            scale_label = f"x10^{{{exponent}}}" # latex format for matplotlib
            new_col_name = f"{y_col} ({scale_label})"
        else:
            new_col_name = y_col
            
        df[new_col_name] = df[y_col] / factor
        scaled_y_cols.append(new_col_name)

    # Melt the dataframe
    # id_vars are all columns except original y_cols and new scaled_y_cols
    # actually, all current columns minus y_cols minus scaled_y_cols are dimensions
    # simpler: id_vars are the 'dims' that remain (or group_dims if we grouped)
    current_dims = [c for c in df.columns if c not in y_cols and c not in scaled_y_cols]
    
    df_melted = df.melt(id_vars=current_dims, value_vars=scaled_y_cols, var_name='Metric', value_name='Value')
    
    # Update args for plotting
    df = df_melted
    # 'Value' is our new Y
    plot_y = 'Value'
    # 'Metric' is a new dimension we should probably use for coloring/differentiation
    if 'Metric' not in args.color_dims:
        args.color_dims.append('Metric')

    # --- Plotting Setup ---
    # Identify roles for each dimension
    assigned_dims = {args.x, plot_y}
    if args.x_subplot: assigned_dims.add(args.x_subplot)
    if args.y_subplot: assigned_dims.add(args.y_subplot)
    if args.color_dims: assigned_dims.update(args.color_dims)
    
    # Split dimensions: All remaining dimensions that are not assigned and not neglected
    # (Since we already averaged out neglected dims, they shouldn't exist in df if we did it right, 
    # but strictly speaking, columns in df now are [group_dims] + [y])
    
    current_cols = set(df.columns)
    # The 'split' dimensions are those that vary but aren't mapped to the plot axes/color
    # These will generate separate files.
    split_dims = list(current_cols - assigned_dims)
    # Sort for deterministic order
    split_dims.sort()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    global_ylim = None
    if args.global_scale:
        # Calculate global limits for consistent scaling across all plots
        y_min = df[plot_y].min()
        y_max = df[plot_y].max()
        
        # Add 5% padding
        y_range = y_max - y_min
        if y_range == 0:
            if y_min != 0:
                 y_padding = 0.1 * abs(y_min)
            else:
                 y_padding = 0.1
        else:
            y_padding = 0.05 * y_range
        
        global_ylim = (y_min - y_padding, y_max + y_padding)
        print(f"Global Y-scale set to: {global_ylim}")

    # Group by split dimensions to generate one plot per group
    # If no split dimensions, we have one group (whole df)
    if split_dims:
        grouped = df.groupby(split_dims)
    else:
        grouped = [('All', df)]

    first_plot = True
    for name, group_df in grouped:
        # Construct filename part from split dims
        if split_dims:
            # name is a tuple of values corresponding to split_dims
            if len(split_dims) == 1:
                vals = [name]
            else:
                vals = name
            
            filename_parts = []
            for dim, val in zip(split_dims, vals):
                filename_parts.append(f"{dim}_{val}")
            
            # Prefix with Y-axis name (replace dots with underscores for filename safety)
            y_prefix = "_".join(y_cols).replace('.', '_')
            base_filename = f"{y_prefix}_{'_'.join(filename_parts)}"
        else:
            y_prefix = "_".join(y_cols).replace('.', '_')
            base_filename = f"{y_prefix}_combined_plot"

        print(f"Generatng plot: {base_filename}...")
        
        # --- Grid Setup ---
        # Get unique row/col values
        row_val_key = args.y_subplot
        col_val_key = args.x_subplot
        
        row_vals = sorted(group_df[row_val_key].unique()) if row_val_key else [None]
        col_vals = sorted(group_df[col_val_key].unique()) if col_val_key else [None]
        
        nrows = len(row_vals)
        ncols = len(col_vals)
        
        # Use plot_y ('Value') for title instead of raw args.y which is list
        title_y_name = "Scaled Metrics" if len(y_cols) > 1 else y_cols[0]
        
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5*ncols + 2, 4*nrows + 1), squeeze=False)
        fig.suptitle(f"{title_y_name} vs {args.x}\n({base_filename})", fontsize=10)
        
        # Markers/Colors cycle
        lines_marker = cycle(['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h'])
        lines_style = cycle(['-', '--', '-.', ':'])
        
        # Iterate through grid
        for i, r_val in enumerate(row_vals):
            for j, c_val in enumerate(col_vals):
                ax = axes[i, j]
                
                # Filter data for this subplot
                sub_df = group_df.copy()
                if row_val_key:
                    sub_df = sub_df[sub_df[row_val_key] == r_val]
                if col_val_key:
                    sub_df = sub_df[sub_df[col_val_key] == c_val]
                
                if sub_df.empty:
                    ax.axis('off')
                    continue
                
                # Title for subplot
                title_parts = []
                if row_val_key: title_parts.append(f"{row_val_key}={r_val}")
                if col_val_key: title_parts.append(f"{col_val_key}={c_val}")
                ax.set_title(", ".join(title_parts), fontsize=9)
                
                # Handle Colors/Lines
                if args.color_dims:
                    # Create a composite key for coloring
                    # group by color dims
                    color_groups = sub_df.groupby(args.color_dims)
                    for c_name, c_group in color_groups:
                        # Label for legend
                        if len(args.color_dims) == 1:
                             label = f"{args.color_dims[0]}={c_name}"
                        else:
                             # c_name is tuple
                             label = ", ".join([f"{d}={v}" for d, v in zip(args.color_dims, c_name)])
                        
                        # Sort by X
                        c_group = c_group.sort_values(by=args.x)
                        ax.plot(c_group[args.x], c_group[plot_y], marker=next(lines_marker), label=label)
                else:
                    # No color dims, just one line
                    sub_df = sub_df.sort_values(by=args.x)
                    ax.plot(sub_df[args.x], sub_df[plot_y], marker='o')
                
                ax.set_xlabel(args.x)
                ax.set_ylabel(args.y_label if args.y_label else "Scaled Value")
                # ax.set_ylabel(args.y) # This line was overwriting the previous one and causing an issue if args.y is a list.

                if args.x_ticks_from_data:
                    unique_x = sorted(sub_df[args.x].unique())
                    ax.set_xticks(unique_x)
                    ax.set_xticklabels(unique_x, rotation=90)

                if args.secondary_x_formula:
                    unique_x = sorted(sub_df[args.x].unique())
                    ax2 = ax.twiny()
                    ax2.set_xlim(ax.get_xlim())
                    ax2.set_xticks(unique_x)
                    secondary_labels = []
                    for xv in unique_x:
                        # Get the first row matching this x value to extract all dimension values
                        row = sub_df[sub_df[args.x] == xv].iloc[0]
                        # Build eval context with all available dimensions
                        eval_ctx = {"x": xv, "np": np}
                        for col in sub_df.columns:
                            if col != plot_y and col != 'Metric':
                                try:
                                    eval_ctx[col] = float(row[col]) if not isinstance(row[col], str) else row[col]
                                except (ValueError, TypeError):
                                    eval_ctx[col] = row[col]
                        try:
                            val = eval(args.secondary_x_formula, {"__builtins__": {}}, eval_ctx)
                            if isinstance(val, float) and val == int(val):
                                val = int(val)
                            secondary_labels.append(str(val))
                        except Exception as e:
                            secondary_labels.append("?")
                    ax2.set_xticklabels(secondary_labels, rotation=90, fontsize=7)
                    ax2.set_xlabel(args.secondary_x_label, fontsize=9)

                if global_ylim:
                    ax.set_ylim(global_ylim)
                ax.grid(True, alpha=0.3)
                
                # Legend (only if multiple lines)
                if args.color_dims:
                    ax.legend(fontsize='small')

        plt.tight_layout()
        
        if args.preview and first_plot:
            print(f"Previewing first plot: {base_filename}")
            plt.show()
            first_plot = False

        out_path = os.path.join(args.output_dir, f"{base_filename}.png")
        plt.savefig(out_path)
        plt.close(fig)
        
    print(f"\nAnalysis complete. Plots saved to '{args.output_dir}'.")

if __name__ == "__main__":
    main()

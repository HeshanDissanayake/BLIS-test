import os
import argparse
import fnmatch
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import sys

def parse_dimensions_from_path(rel_dir_path):
    """
    Parses dimensions from a relative directory path.
    Expected format for each directory: NameValue or Name_Value (e.g., L1_32, LW16).
    """
    dims = {}
    parts = rel_dir_path.split(os.sep)
    
    # Regex to capture Name and Value. 
    pattern = re.compile(r'^([A-Za-z0-9]+?)(_?)(\d+)$')  

    for part in parts:
        if part == '.': continue
        match = pattern.match(part)
        if match:
            name = match.group(1)
            value = int(match.group(3))
            dims[name] = value

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
            
            df.columns = df.columns.str.strip()
            
            if y_col not in df.columns:
                print(f"Column '{y_col}' not found in {full_path}. Skipping.", file=sys.stderr)
                continue
                
            # Calculate average
            y_val = df[y_col].mean()
            
            # Store record
            record = dims.copy()
            record['y_value_avg'] = y_val
            record['source_file'] = full_path 
            data_records.append(record)
            
    return pd.DataFrame(data_records)

class InteractiveExplorer:
    def __init__(self, df, x_dim, y_dim_label, neglect_dims=None):
        self.df = df
        self.x_dim = x_dim
        self.y_dim_label = y_dim_label
        
        # Identify slider dimensions
        # All columns except x_dim, y_value_avg, source_file, and neglected ones
        exclude = {x_dim, 'y_value_avg', 'source_file'}
        if neglect_dims:
            exclude.update(neglect_dims)
            
        self.slider_dims = [c for c in df.columns if c not in exclude]
        self.slider_dims.sort()
        
        # Prepare unique values
        self.dim_values = {}
        self.sliders = {}
        
        for dim in self.slider_dims:
            vals = sorted(df[dim].unique())
            self.dim_values[dim] = vals

        # Setup Figure
        # Calculate space needed for sliders
        # 0.04 height per slider
        slider_area_height = len(self.slider_dims) * 0.05
        bottom_margin = max(0.15, slider_area_height + 0.05)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(left=0.1, bottom=bottom_margin, top=0.95, right=0.95)
        
        # Create Sliders
        # Place them from top of bottom area downwards or bottom up.
        # Let's go from bottom margin downwards.
        
        for i, dim in enumerate(self.slider_dims):
            vals = self.dim_values[dim]
            # axes position: [left, bottom, width, height]
            # bottom starts at bottom_margin - (i+1)*gap
            slider_y = bottom_margin - (i + 1) * 0.04
            
            ax_s = plt.axes([0.25, slider_y, 0.60, 0.03])
            
            # Create discrete slider logic
            # Range 0 to len-1
            s = Slider(
                ax=ax_s,
                label=dim,
                valmin=0,
                valmax=len(vals) - 1,
                valinit=0,
                valstep=1,
            )
            
            # Store reference
            self.sliders[dim] = s
            
            # Set initial text
            s.valtext.set_text(str(vals[0]))
            
            # Connect callback
            s.on_changed(self.update_plot)
            
        self.update_plot()
        plt.show()

    def update_plot(self, val=None):
        # Clear current plot
        self.ax.clear()
        
        # Filter dataframe based on all sliders
        subset = self.df.copy()
        
        title_info = []
        for dim in self.slider_dims:
            s = self.sliders[dim]
            idx = int(s.val)
            val_list = self.dim_values[dim]
            
            # Safety check
            if idx >= len(val_list): idx = len(val_list) - 1
            
            actual_val = val_list[idx]
            
            # Update label text to real value
            s.valtext.set_text(str(actual_val))
            
            # Filter
            subset = subset[subset[dim] == actual_val]
            title_info.append(f"{dim}={actual_val}")

        # Handle X and Y
        if subset.empty:
            self.ax.text(0.5, 0.5, "No Data found for this combination", ha='center', va='center', transform=self.ax.transAxes)
        else:
            # Sort by X
            subset = subset.sort_values(by=self.x_dim)
            
            # Plot
            self.ax.plot(subset[self.x_dim], subset['y_value_avg'], marker='o', linestyle='-', color='b')
            self.ax.set_xlabel(self.x_dim)
            self.ax.set_ylabel(self.y_dim_label)
            self.ax.set_title(f"{self.y_dim_label} vs {self.x_dim}")
            self.ax.grid(True)
            
        self.fig.canvas.draw_idle()


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
                continue 
    return [], []

def main():
    parser = argparse.ArgumentParser(description="Interactive CSV Analysis Explorer")
    parser.add_argument("--csv_file", required=True, help="Pattern for CSV file name (e.g., data_*.csv)")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--x", help="Dimension to use for X axis")
    parser.add_argument("--y", help="CSV Column to average for Y axis")
    parser.add_argument("--neglect_dims", nargs='+', help="List of dimensions to ignore (average over)")
    parser.add_argument("--list_params", action="store_true", help="List available dimensions and columns")

    args = parser.parse_args()
    
    if args.list_params:
        print(f"Scanning {args.root} for parameters...")
        dims, cols = get_available_params(args.root, args.csv_file)
        print("Dims:", dims)
        print("Cols:", cols)
        return

    if not args.x or not args.y:
        parser.error("--x and --y are required")

    print("Scanning and collecting data... (this might take a moment)")
    df = scan_and_collect_data(args.root, args.csv_file, args.x, args.y)
    
    if df.empty:
        print("No data found.")
        return
        
    # Handle neglect dims
    if args.neglect_dims:
        if args.x in args.neglect_dims:
            args.neglect_dims.remove(args.x)
            
        dims_to_drop = [d for d in args.neglect_dims if d in df.columns]
        if dims_to_drop:
             if 'source_file' in df.columns:
                 df = df.drop(columns=['source_file'])
             group_cols = [c for c in df.columns if c not in dims_to_drop and c != 'y_value_avg']
             if group_cols:
                 print(f"Aggregating over {dims_to_drop}...")
                 df = df.groupby(group_cols, as_index=False)['y_value_avg'].mean()

    print("Starting interactive view...")
    InteractiveExplorer(df, args.x, args.y, neglect_dims=args.neglect_dims)

if __name__ == "__main__":
    main()

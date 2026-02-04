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
    Expected format: NameValue or Name_Value
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

def scan_and_collect_data(root_dir, csv_file_pattern, x_dim, y_col):
    data_records = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, csv_file_pattern):
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(dirpath, root_dir)
            dims = parse_dimensions_from_path(rel_path)
            
            try:
                df = pd.read_csv(full_path)
            except Exception as e:
                # print(f"Error reading {full_path}: {e}", file=sys.stderr)
                continue
            
            df.columns = df.columns.str.strip()
            
            if y_col not in df.columns:
                continue
                
            y_val = df[y_col].mean()
            record = dims.copy()
            record['y_value_avg'] = y_val
            record['source_file'] = full_path 
            data_records.append(record)
            
    return pd.DataFrame(data_records)

class InteractiveSubplotExplorer:
    def __init__(self, df, x_dim, y_dim_label, x_subplot=None, y_subplot=None, neglect_dims=None):
        self.df = df
        self.x_dim = x_dim
        self.y_dim_label = y_dim_label
        self.x_subplot = x_subplot
        self.y_subplot = y_subplot
        
        # Determine slider dimensions
        exclude = {x_dim, 'y_value_avg', 'source_file'}
        if x_subplot: exclude.add(x_subplot)
        if y_subplot: exclude.add(y_subplot)
        if neglect_dims: exclude.update(neglect_dims)
            
        self.slider_dims = [c for c in df.columns if c not in exclude]
        self.slider_dims.sort()
        
        # Prepare unique values for sliders
        self.dim_values = {}
        self.sliders = {}
        for dim in self.slider_dims:
            vals = sorted(df[dim].unique())
            self.dim_values[dim] = vals

        # Prepare Subplot Grid values
        self.row_vals = [None]
        self.col_vals = [None]
        
        if y_subplot:
            self.row_vals = sorted(df[y_subplot].unique())
        if x_subplot:
            self.col_vals = sorted(df[x_subplot].unique())
            
        self.nrows = len(self.row_vals)
        self.ncols = len(self.col_vals)
        
        # Setup Figure
        slider_area_height = len(self.slider_dims) * 0.04 + 0.05
        # Ensure at least some plot area
        if slider_area_height > 0.4: slider_area_height = 0.4
        
        # Adjust figure size based on grid
        fig_width = max(10, 4 * self.ncols)
        fig_height = max(8, 3 * self.nrows)
        
        self.fig, self.axes_grid = plt.subplots(
            nrows=self.nrows, ncols=self.ncols, 
            figsize=(fig_width, fig_height),
            squeeze=False, sharex=True, sharey=True
        )
        
        # Adjust layout to make room for sliders at the bottom
        plt.subplots_adjust(left=0.1, bottom=slider_area_height + 0.1, top=0.95, right=0.95)
        
        # Create Sliders in the bottom area
        for i, dim in enumerate(self.slider_dims):
            vals = self.dim_values[dim]
            slider_y = (slider_area_height + 0.05) - (i + 1) * 0.04
            
            if slider_y < 0.01: slider_y = 0.01 # Safety margin
            
            ax_s = plt.axes([0.25, slider_y, 0.60, 0.03])
            
            # If only 1 val, slider is just a display
            valmax = max(0, len(vals) - 1)
            
            s = Slider(
                ax=ax_s,
                label=dim,
                valmin=0,
                valmax=valmax,
                valinit=0,
                valstep=1,
            )
            self.sliders[dim] = s
            s.valtext.set_text(str(vals[0]))
            s.on_changed(self.update_plot)
            
        self.update_plot()
        plt.show()

    def update_plot(self, val=None):
        # 1. Filter global dataframe based on sliders
        current_df = self.df.copy()
        
        slider_title_parts = []
        for dim in self.slider_dims:
            s = self.sliders[dim]
            idx = int(s.val)
            val_list = self.dim_values[dim]
            if idx >= len(val_list): idx = len(val_list) - 1
            actual_val = val_list[idx]
            
            s.valtext.set_text(str(actual_val))
            current_df = current_df[current_df[dim] == actual_val]
            slider_title_parts.append(f"{dim}={actual_val}")

        # 2. Iterate through grid
        for i, r_val in enumerate(self.row_vals):
            for j, c_val in enumerate(self.col_vals):
                ax = self.axes_grid[i, j]
                ax.clear()
                
                # Filter for this subplot
                subset = current_df.copy()
                subplot_title = []
                
                if self.y_subplot:
                    subset = subset[subset[self.y_subplot] == r_val]
                    subplot_title.append(f"{self.y_subplot}={r_val}")
                if self.x_subplot:
                    subset = subset[subset[self.x_subplot] == c_val]
                    subplot_title.append(f"{self.x_subplot}={c_val}")
                
                # Plot
                if subset.empty:
                    ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes, fontsize=8)
                else:
                    subset = subset.sort_values(by=self.x_dim)
                    ax.plot(subset[self.x_dim], subset['y_value_avg'], marker='o', linestyle='-', color='b')
                    ax.grid(True)
                
                # Labels/Titles
                if subplot_title:
                   ax.set_title(", ".join(subplot_title), fontsize=10)
                
                if i == self.nrows - 1:
                    ax.set_xlabel(self.x_dim)
                if j == 0:
                    ax.set_ylabel(self.y_dim_label)
        
        # Set super title with slider configs
        self.fig.suptitle(f"{self.y_dim_label} vs {self.x_dim}\n" + ", ".join(slider_title_parts), fontsize=12)
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
            except Exception:
                continue 
    return [], []

def main():
    parser = argparse.ArgumentParser(description="Interactive CSV Analyis with Subplots")
    parser.add_argument("--csv_file", required=True, help="Pattern for CSV file name")
    parser.add_argument("--root", required=True, help="Root directory")
    parser.add_argument("--x", required=True, help="X axis dimension")
    parser.add_argument("--y", required=True, help="Y axis column")
    parser.add_argument("--x_subplot", help="Dimension for subplot columns")
    parser.add_argument("--y_subplot", help="Dimension for subplot rows")
    parser.add_argument("--neglect_dims", nargs='+', help="Dimensions to average over")
    parser.add_argument("--list_params", action="store_true", help="List dims")

    args = parser.parse_args()
    
    if args.list_params:
        print("Scanning...")
        dims, cols = get_available_params(args.root, args.csv_file)
        print("Dims:", dims)
        print("Cols:", cols)
        return

    print("Collecting data...")
    df = scan_and_collect_data(args.root, args.csv_file, args.x, args.y)
    
    if df.empty:
        print("No data found.")
        return
        
    # Handle neglect
    if args.neglect_dims:
        ignore_list = args.neglect_dims
        # Protect structural dims
        for d in [args.x, args.x_subplot, args.y_subplot]:
            if d and d in ignore_list:
                ignore_list.remove(d)
                
        dims_to_drop = [d for d in ignore_list if d in df.columns]
        if dims_to_drop:
             if 'source_file' in df.columns:
                 df = df.drop(columns=['source_file'])
             group_cols = [c for c in df.columns if c not in dims_to_drop and c != 'y_value_avg']
             if group_cols:
                 print(f"Aggregating over {dims_to_drop}...")
                 df = df.groupby(group_cols, as_index=False)['y_value_avg'].mean()

    print("Starting interactive subplot explorer...")
    InteractiveSubplotExplorer(df, args.x, args.y, x_subplot=args.x_subplot, y_subplot=args.y_subplot, neglect_dims=args.neglect_dims)

if __name__ == "__main__":
    main()

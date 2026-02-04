#!/usr/bin/env python3
import os
import sys
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import glob

def parse_dir_name(dirname):
    """
    Parses a directory name to extract the dimension key and value.
    Matches strict pattern: Label (alphabetic) + optional '_' + Value (numeric).
    Example: 'L1_32' -> ('L1', 32), 'MC4096' -> ('MC', 4096).
    """
    match = re.match(r"^([a-zA-Z]+)_?(\d+)$", dirname)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def get_dimensions_from_path(file_path, root_dir):
    """
    Extracts dimensions from the file path relative to the root directory.
    """
    rel_path = os.path.relpath(file_path, root_dir)
    # Remove the filename to get just the folders
    dir_path = os.path.dirname(rel_path)
    if dir_path == "":
        return {}
    
    dims = {}
    # Split path into components
    parts = Path(dir_path).parts
    
    for part in parts:
        key, value = parse_dir_name(part)
        if key:
            dims[key] = value
        else:
            # If a folder doesn't match the pattern, we currently ignore it but warn user
            print(f"Warning: Directory '{part}' in path '{rel_path}' does not match dimension pattern (Label_Number).")
    
    return dims

def main():
    parser = argparse.ArgumentParser(description="CSV Analysis and Plotting Tool")
    parser.add_argument("--csv_file", required=True, help="Name of the CSV file to find")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--x", required=True, help="Column name for X axis")
    parser.add_argument("--y", required=True, help="Column name for Y axis")
    parser.add_argument("--subplot_x", required=True, help="Dimension name for subplot X axis (columns)")
    parser.add_argument("--subplot_y", required=True, help="Dimension name for subplot Y axis (rows)")
    parser.add_argument("--output_dir", default="plots_out", help="Directory to save output plots")
    parser.add_argument("--plot_type", default="line", choices=["line", "scatter", "bar"], help="Type of plot to generate")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    if not root_path.exists():
        sys.exit(f"Error: Root directory '{args.root}' does not exist.")

    print(f"Scanning '{args.root}' for '{args.csv_file}'...")
    
    # 1. Scan for files
    found_files = [] 
    # glob pattern to find files recursively. generic pattern matching check later name check for exact match
    for path in root_path.rglob(args.csv_file):
        if path.name == args.csv_file:
            dims = get_dimensions_from_path(path, args.root)
            
            # Check if required subplot dims are present
            if args.subplot_x not in dims:
                sys.exit(f"Error: Subplot dimension '{args.subplot_x}' not found in path for file: {path}")
            if args.subplot_y not in dims:
                sys.exit(f"Error: Subplot dimension '{args.subplot_y}' not found in path for file: {path}")
                
            found_files.append({
                "path": path,
                "dims": dims
            })
            
    if not found_files:
        sys.exit(f"Error: No files named '{args.csv_file}' found in '{args.root}'.")
        
    print(f"Found {len(found_files)} matching CSV files.")

    # 2. Group files by "remaining dimensions"
    # The grouping key is a frozen set of (key, value) pairs excluding subplot_x and subplot_y
    groups = defaultdict(list)
    
    for entry in found_files:
        dims = entry["dims"]
        # Extract remaining dimensions
        remaining_dims = {k: v for k, v in dims.items() if k not in [args.subplot_x, args.subplot_y]}
        
        # Create a hashable key for the dictionary
        # Sorting ensures consistent key order
        group_key = tuple(sorted(remaining_dims.items()))
        groups[group_key].append(entry)
        
    # 3. Process each group
    output_root = Path(args.output_dir)
    
    for group_key, entries in groups.items():
        # Reconstruct the grouping dict
        group_dims = dict(group_key)
        
        # Determine grid dimensions for this group
        sp_x_values = sorted(list(set(e["dims"][args.subplot_x] for e in entries)))
        sp_y_values = sorted(list(set(e["dims"][args.subplot_y] for e in entries)))
        
        if not sp_x_values or not sp_y_values:
             continue

        # Prepare Figure
        nrows = len(sp_y_values)
        ncols = len(sp_x_values)
        
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10 * ncols, 4 * nrows), constrained_layout=True)
        
        # Ensure axes is always array-like for indexing, even if 1x1
        if nrows == 1 and ncols == 1:
            axes = [[axes]]
        elif nrows == 1:
            axes = [axes]
        elif ncols == 1:
            axes = [[ax] for ax in axes]
            
        # Prepare a list to collect data for the combined plot
        collected_data = []

        # Plotting Loop
        for r, y_val in enumerate(sp_y_values):
            for c, x_val in enumerate(sp_x_values):
                ax = axes[r][c]
                
                # Find the specific file for this cell coordinates
                match_entry = next((e for e in entries if e["dims"][args.subplot_x] == x_val and e["dims"][args.subplot_y] == y_val), None)
                
                if match_entry:
                    try:
                        df = pd.read_csv(match_entry["path"])
                        
                        # Check columns
                        if args.x not in df.columns:
                            sys.exit(f"Error: Column '{args.x}' not found in {match_entry['path']}")
                        if args.y not in df.columns:
                            sys.exit(f"Error: Column '{args.y}' not found in {match_entry['path']}")
                        
                        # Store df for combined plotting
                        collected_data.append((f"{args.subplot_x}={x_val}, {args.subplot_y}={y_val}", df))

                        # Plot
                        if args.plot_type == "line":
                            ax.plot(df[args.x], df[args.y], marker='o')
                        elif args.plot_type == "scatter":
                            ax.scatter(df[args.x], df[args.y])
                        elif args.plot_type == "bar":
                            ax.bar(df[args.x], df[args.y], width=0.8)
                            
                        ax.set_title(f"{args.subplot_x}={x_val}, {args.subplot_y}={y_val}")
                        ax.set_xlabel(args.x)
                        ax.set_ylabel(args.y)
                        # ax.set_ylim(0, 800000)
                        ax.grid(True)
                        
                    except Exception as e:
                        print(f"Error processing {match_entry['path']}: {e}")
                else:
                    # No data for this specific subplot combination
                    ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                    ax.axis('off')

        # Add a super title with common dimensions
        title_str = ", ".join([f"{k}={v}" for k, v in group_dims.items()])
        fig.suptitle(f"Analysis: {title_str}", fontsize=14)
        
        # 4. Save Output
        # Construct directory path based on group dimensions
        # Order keys alphabetically for consistent path structure
        path_parts = [f"{k}_{v}" for k, v in sorted(group_dims.items())]
        save_dir = output_root.joinpath(*path_parts)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = save_dir / "plot.png"
        print(f"Saving plot to: {save_path}")
        plt.savefig(save_path)
        plt.close(fig)

        # 5. Save Combined Plot
        if collected_data:
            fig_comb, ax_comb = plt.subplots(figsize=(14, 8), constrained_layout=True)
            
            averages_text = []
            
            for label, df in collected_data:
                # Calculate average
                try:
                    avg_val = df[args.y].mean()
                    averages_text.append(f"Avg {label} :: {avg_val:.2f}")
                except:
                    pass

                # Use line plot for combined view if bar was selected, for better visibility
                if args.plot_type == "scatter":
                    ax_comb.scatter(df[args.x], df[args.y], label=label, alpha=0.7)
                else:
                    # Default to line for bar/line types for comparison
                    ax_comb.plot(df[args.x], df[args.y], label=label, alpha=0.7)
            
            ax_comb.set_title(f"Combined Analysis: {title_str}")
            ax_comb.set_xlabel(args.x)
            ax_comb.set_ylabel(args.y)
            # ax_comb.set_ylim(0, 800000)
            ax_comb.grid(True)
            ax_comb.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

            # Add statistics text below the legend (positioned at bottom right area)
            if averages_text:
                stats_str = "\n".join(averages_text)
                ax_comb.text(1.05, 0.0, stats_str, transform=ax_comb.transAxes, 
                             ha='left', va='bottom', fontsize=9, 
                             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='lightgray'))
            
            save_path_comb = save_dir / "plot_combined.png"
            print(f"Saving combined plot to: {save_path_comb}")
            plt.savefig(save_path_comb)
            plt.close(fig_comb)

    print("Processing complete.")

if __name__ == "__main__":
    main()
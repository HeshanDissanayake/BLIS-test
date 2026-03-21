#!/usr/bin/env python3
"""
3D_heatmap_json.py

Plots 3D bar charts from hierarchical JSON experiment data.

Dimensions inferred from directory names (e.g. MC4096/KC64/MR8) are mapped to:
  --x      → x-axis          (a directory dimension, e.g. MR)
  --y      → y-axis          (a directory dimension, e.g. NR)
  --z      → z-axis height   (a JSON metric or formula)
  --color  → bar color       (optional, defaults to z value)

Subplot grid and output options mirror heatmap_json.py.
"""

import os
import re
import json
import argparse
import sys
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
import matplotlib.colors as mcolors


# ---------------------------------------------------------------------------
# Shared helpers (copied from heatmap_json.py)
# ---------------------------------------------------------------------------

def parse_folder_name(folder_name):
    match_underscore = re.match(r"^([a-zA-Z0-9_]+)_([a-zA-Z0-9\.]+)$", folder_name)
    if match_underscore:
        return match_underscore.group(1), match_underscore.group(2)
    match_concat = re.match(r"^([a-zA-Z]+)(\d+(?:\.\d+)?)$", folder_name)
    if match_concat:
        return match_concat.group(1), match_concat.group(2)
    return None, None


def get_json_value(data, key_path):
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


def is_formula(value_str):
    """Check if the value string looks like a formula (contains operators or parentheses)."""
    return any(op in value_str for op in ['+', '-', '*', '/', '(', ')'])


def sanitize_filename(filename):
    """Remove or replace characters invalid in filenames."""
    # Replace problematic characters with underscores
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '(', ')']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Clean up multiple underscores
    while '__' in filename:
        filename = filename.replace('__', '_')
    return filename


def evaluate_formula(formula, record, json_data, allow_missing=False):
    """
    Evaluate a formula using directory dimensions and/or JSON values.
    Supports math functions: floor, ceil, sqrt, sin, cos, log, etc.
    """
    import ast
    import re
    
    # Start with a copy of the record (directory dimensions)
    context = record.copy()
    
    # Add flattened JSON values to context
    if json_data:
        flattened = flatten_json(json_data)
        context.update(flattened)
    
    # Add math functions to context
    math_funcs = {
        'floor': math.floor,
        'ceil': math.ceil,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'abs': abs,
        'pow': pow,
        'round': round,
    }
    context.update(math_funcs)
    
    # Extract variable names from formula
    variable_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_.-]*(?:\.[a-zA-Z0-9_.-]+)*|[a-zA-Z_][a-zA-Z0-9_]*)\b'
    all_identifiers = set(re.findall(variable_pattern, formula))
    
    # Filter to get only variables (not math functions)
    required_vars = all_identifiers - set(math_funcs.keys())
    
    # Check for missing variables
    missing_vars = required_vars - set(context.keys())
    
    if missing_vars and not allow_missing:
        available_dir = set(record.keys())
        available_json = set(flatten_json(json_data).keys()) if json_data else set()
        raise ValueError(
            f"Formula '{formula}' references undefined variable(s): {', '.join(sorted(missing_vars))}\n"
            f"Available directory dimensions: {', '.join(sorted(available_dir)) or '(none)'}\n"
            f"Available JSON metrics: {', '.join(sorted(available_json)) or '(none)'}"
        )
    
    try:
        # Use eval with restricted namespace for safety
        result = eval(formula, {"__builtins__": {}}, context)
        return result if result is not None else np.nan
    except (TypeError, ZeroDivisionError, ValueError) as e:
        # Calculation error (not missing variable)
        raise ValueError(f"Error evaluating formula '{formula}': {e}")


def collect_data(root_dir, target_value_key=None, target_formula=None, list_mode=False):
    data_records = []

    if not os.path.exists(root_dir):
        print(f"Error: Root directory '{root_dir}' does not exist.")
        sys.exit(1)

    print(f"Scanning directory: {root_dir}...")

    for dirpath, dirnames, filenames in os.walk(root_dir):
        json_files = [f for f in filenames if f.endswith('.json')]

        for j_file in json_files:
            file_path = os.path.join(dirpath, j_file)

            rel_path = os.path.relpath(dirpath, root_dir)
            path_parts = rel_path.split(os.sep)

            record = {}
            for part in path_parts:
                if part == '.':
                    continue
                k, v = parse_folder_name(part)
                if k:
                    try:
                        v = float(v) if '.' in v else int(v)
                    except (ValueError, TypeError):
                        pass
                    record[k] = v

            try:
                with open(file_path, 'r') as f:
                    json_data = json.load(f)

                if list_mode:
                    flattened = flatten_json(json_data)
                    return list(record.keys()), list(flattened.keys())

                # Determine what to store as the value
                stored_value_key = target_formula if target_formula else target_value_key
                
                if stored_value_key:
                    if target_formula:
                        # Use formula
                        try:
                            val = evaluate_formula(target_formula, record, json_data, allow_missing=False)
                        except ValueError as ve:
                            print(f"Error: {ve}")
                            sys.exit(1)
                    else:
                        # Use simple value (directory dimension or JSON)
                        if target_value_key in record:
                            val = record[target_value_key]
                        else:
                            val = get_json_value(json_data, target_value_key)
                            if val is None:
                                available_dir = set(record.keys())
                                available_json = set(flatten_json(json_data).keys()) if json_data else set()
                                print(f"Error: Cannot resolve '{target_value_key}'")
                                print(f"Available directory dimensions: {', '.join(sorted(available_dir)) or '(none)'}")
                                print(f"Available JSON metrics: {', '.join(sorted(available_json)) or '(none)'}")
                                sys.exit(1)
                    record[stored_value_key] = val if val is not None else np.nan

                data_records.append(record)

            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")

    return data_records


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot 3D bar charts of a JSON metric over two directory dimensions."
    )

    # Data
    parser.add_argument("--root",    required=True, help="Base directory to scan.")
    parser.add_argument("--x",       help="Directory dimension mapped to x-axis.")
    parser.add_argument("--y",       help="Directory dimension mapped to y-axis.")
    parser.add_argument("--value",   help="Z-axis (height) value: directory dimension or JSON metric.")
    parser.add_argument("--formula", help="Formula to compute z-value from --value and other variables.")

    # Subplot grid
    parser.add_argument("--x_subplot", help="Dimension to map to subplot columns.")
    parser.add_argument("--y_subplot", help="Dimension to map to subplot rows.")

    # Processing
    parser.add_argument("--list_params", action="store_true",
                        help="List all available dimensions and JSON keys, then exit.")

    # Display / output
    parser.add_argument("--output_dir",   default="plots_3d",
                        help="Directory to save output plots (default: 'plots_3d').")
    parser.add_argument("--preview",      action="store_true",
                        help="Show the first plot in a window.")
    parser.add_argument("--global_scale", action="store_true",
                        help="Use the same z-scale (min/max) across all plots.")
    parser.add_argument("--value_label",  help="Custom label for the z-axis/colorbar.")
    parser.add_argument("--cmap",         default="viridis",
                        help="Matplotlib colormap name (default: 'viridis').")
    parser.add_argument("--azim",         type=int, default=-60,
                        help="Azimuthal viewing angle (default: -60).")
    parser.add_argument("--elev",         type=int, default=30,
                        help="Elevation viewing angle (default: 30).")

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # ---- list_params mode ----
    if args.list_params:
        path_dims, json_dims = collect_data(args.root, list_mode=True)
        if path_dims is None:
            print("No JSON files or parseable directories found.")
        else:
            print("\nAvailable Directory Dimensions (Parameters):")
            for d in sorted(set(path_dims)):
                print(f"  - {d}")
            print("\nAvailable JSON Keys (Metrics):")
            for d in sorted(json_dims):
                print(f"  - {d}")
        return

    # ---- Validation ----
    for flag, name in [("--x", args.x), ("--y", args.y), ("--value", args.value)]:
        if not name:
            print(f"Error: {flag} is required (unless using --list_params).")
            sys.exit(1)

    # ---- Collect ----
    records = collect_data(args.root, target_value_key=args.value, target_formula=args.formula)
    if not records:
        print("No data found.")
        sys.exit(1)

    df = pd.DataFrame(records)
    # Determine which key to use for the dataframe column
    value_col = args.formula if args.formula else args.value
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
    print(f"Loaded {len(df)} records.")

    # ---- Global color scale ----
    global_vmin = global_vmax = None
    if args.global_scale:
        global_vmin = df[value_col].min()
        global_vmax = df[value_col].max()
        print(f"Global z-scale: vmin={global_vmin:.4g}, vmax={global_vmax:.4g}")

    os.makedirs(args.output_dir, exist_ok=True)

    value_label   = args.value_label if args.value_label else (args.formula if args.formula else args.value)
    base_filename_key = args.formula if args.formula else args.value
    base_filename = f"heatmap3d_{sanitize_filename(base_filename_key)}"

    print(f"Generating plot: {base_filename}...")

    # ---- Subplot grid (only when explicitly requested) ----
    row_vals = sorted(df[args.y_subplot].unique()) if args.y_subplot else [None]
    col_vals = sorted(df[args.x_subplot].unique()) if args.x_subplot else [None]
    nrows = len(row_vals)
    ncols = len(col_vals)

    # Increase figure size for 3D subplots
    fig = plt.figure(figsize=(8 * ncols + 2, 6 * nrows + 1))
    fig.suptitle(
        f"{value_label}  |  rows={args.y}  cols={args.x}\n({base_filename})",
        fontsize=14
    )

    colormap = plt.get_cmap(args.cmap)
    mappable = None # To hold the ScalarMappable for colorbar

    for i, r_val in enumerate(row_vals):
        for j, c_val in enumerate(col_vals):
            # Add subplot with 3d projection
            ax = fig.add_subplot(nrows, ncols, i * ncols + j + 1, projection='3d')

            sub = df.copy()
            if args.y_subplot:
                sub = sub[sub[args.y_subplot] == r_val]
            if args.x_subplot:
                sub = sub[sub[args.x_subplot] == c_val]

            if sub.empty:
                ax.axis('off')
                continue

            try:
                pivot = sub.pivot_table(
                    index=args.y, columns=args.x,
                    values=value_col, aggfunc='mean'
                )
            except Exception as e:
                print(f"  Warning: pivot failed for subplot ({r_val},{c_val}): {e}")
                ax.axis('off')
                continue

            # Sort axes
            pivot = pivot.sort_index(axis=0) # y-axis
            pivot = pivot.sort_index(axis=1) # x-axis

            # Prepare 3D data
            _x_labels = pivot.columns
            _y_labels = pivot.index
            _x = np.arange(len(_x_labels))
            _y = np.arange(len(_y_labels))
            _xx, _yy = np.meshgrid(_x, _y)
            x, y = _xx.ravel(), _yy.ravel()

            top = pivot.values.ravel()
            bottom = np.zeros_like(top)
            width = depth = 0.8 # Bar width/depth range [0, 1]

            # Mask NaN values
            mask = ~np.isnan(top)
            x = x[mask]
            y = y[mask]
            top = top[mask]
            bottom = bottom[mask]

            if len(top) == 0:
                ax.axis('off')
                continue

            # Determine colors based on height
            if args.global_scale:
                vmin, vmax = global_vmin, global_vmax
            else:
                vmin, vmax = top.min(), top.max()
            
            # Use a norm to map values to colors
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
            colors = colormap(norm(top))
            
            # Keep mappable for colorbar (overwrite with last one)
            mappable = cm.ScalarMappable(norm=norm, cmap=colormap)

            ax.bar3d(x, y, bottom, width, depth, top, shade=True, color=colors)

            # Labels and Ticks
            ax.set_xlabel(args.x, fontsize=12)
            ax.set_ylabel(args.y, fontsize=12)
            ax.set_zlabel(value_label, fontsize=12)

            ax.set_xticks(_x + width/2)
            ax.set_xticklabels([str(l) for l in _x_labels], rotation=45, ha='right')
            
            ax.set_yticks(_y + depth/2)
            ax.set_yticklabels([str(l) for l in _y_labels])

            # View Angle
            ax.view_init(elev=args.elev, azim=args.azim)

            # Subplot title
            title_parts = []
            if args.y_subplot:
                title_parts.append(f"{args.y_subplot}={r_val}")
            if args.x_subplot:
                title_parts.append(f"{args.x_subplot}={c_val}")
            ax.set_title(", ".join(title_parts), fontsize=14)

    # Global Colorbar
    if mappable:
        fig.subplots_adjust(right=0.88)
        cbar_ax = fig.add_axes([0.91, 0.1, 0.02, 0.8])
        cbar = fig.colorbar(mappable, cax=cbar_ax)
        cbar.set_label(value_label, fontsize=14)
        cbar.ax.tick_params(labelsize=12)

    plt.tight_layout(rect=[0, 0, 0.90, 0.95])

    if args.preview:
        print(f"Previewing: {base_filename}")
        plt.show()

    # Ensure subdirectories exist
    png_dir = os.path.join(args.output_dir, "png")
    pdf_dir = os.path.join(args.output_dir, "pdf")
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    # Save PNG
    png_path = os.path.join(png_dir, f"{base_filename}.png")
    plt.savefig(png_path, dpi=150)
    print(f"  Saved → {png_path}")

    # Save PDF
    pdf_path = os.path.join(pdf_dir, f"{base_filename}.pdf")
    plt.savefig(pdf_path, format="pdf", dpi=150)
    print(f"  Saved → {pdf_path}")

    plt.close(fig)
    print(f"\nDone. Plots saved to '{args.output_dir}'.")


if __name__ == "__main__":
    main()

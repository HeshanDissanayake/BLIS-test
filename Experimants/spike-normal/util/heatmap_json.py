#!/usr/bin/env python3
"""
heatmap_json.py

Plots heatmaps from hierarchical JSON experiment data.

Dimensions inferred from directory names (e.g. MC4096/KC64/MR8) are mapped to:
  --x      → heatmap columns  (a directory dimension, e.g. MR)
  --y      → heatmap rows     (a directory dimension, e.g. NR)
  --value  → heatmap cell color  (a JSON metric, e.g. stats.miss_rate)

Subplot grid and output options mirror analyse_json.py so both tools can be
driven from the same experiment runner.
Each directory path is treated as an independent data point. No averaging or
dimension-splitting is applied; if subplots are not given, one single heatmap
is produced directly from all collected data.
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
import matplotlib.colors as mcolors


# ---------------------------------------------------------------------------
# Shared helpers (copied from analyse_json.py so the file is self-contained)
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
    Example: 'KC*2' or 'MC+KC' or 'floor(NR*MR+MR+NR)' or 'stats.miss_rate*100'
    
    Args:
        formula: The formula string to evaluate
        record: Dictionary of directory dimensions
        json_data: Dictionary of JSON data
        allow_missing: If False, raises error on missing variables. If True, returns np.nan
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
        'min': min,  # Supported built-in
        'max': max,  # Supported built-in
    }
    context.update(math_funcs)
    
    # Extract variable names from formula (identifiers that aren't math functions)
    # Handle both simple variables (KC, MR) and JSON paths with hyphens/dots (l1-i_dcaches.bytes_to_memory)
    # Match: word chars OR word chars with embedded hyphens/dots if they contain at least one dot
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
    
    # Prepare formula for eval() by replacing special keys (with dots/hyphens) with safe identifiers
    # We strip out variables that are just math functions or not in context (if allow_missing=True)
    eval_context = context.copy()
    eval_formula = formula

    # Sort variables by length (descending) so we replace longer matches first 
    # (e.g. replace 'stats.miss_rate' before 'mr' if both exist)
    sorted_vars = sorted(required_vars, key=len, reverse=True)
    
    for var in sorted_vars:
        if var in context:
            # Generate a safe Python identifier
            # Hex digest is safest to avoid collisions with existing vars or other replacements
            import hashlib
            safe_id = "v_" + hashlib.md5(var.encode()).hexdigest()
            
            # Map the safe ID to the actual value in the context
            eval_context[safe_id] = context[var]
            
            # Replace the variable in the formula with the safe ID
            # Use lookbehind/lookahead to ensure we match whole 'words' as defined by our loose variable pattern
            # Note: We must escape the var string because it contains dots/special chars
            pattern = r'(?<![a-zA-Z0-9_.-])' + re.escape(var) + r'(?![a-zA-Z0-9_.-])'
            eval_formula = re.sub(pattern, safe_id, eval_formula)

    try:
        # Use eval with restricted namespace for safety
        result = eval(eval_formula, {"__builtins__": {}}, eval_context)
        return result if result is not None else np.nan
    except (TypeError, ZeroDivisionError, ValueError, SyntaxError) as e:
        # Calculation error (not missing variable)
        raise ValueError(f"Error evaluating formula '{formula}' (mapped to '{eval_formula}'): {e}")


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
        description="Plot heatmaps of a JSON metric over two directory dimensions."
    )

    # Data
    parser.add_argument("--root",    required=True, help="Base directory to scan.")
    parser.add_argument("--x",       help="Directory dimension mapped to heatmap columns.")
    parser.add_argument("--y",       help="Directory dimension mapped to heatmap rows.")
    parser.add_argument("--value",   help="Heatmap cell color value: directory dimension (e.g. 'KC') or JSON metric (e.g. 'stats.miss_rate').")
    parser.add_argument("--formula", help="Formula to compute cell color from --value and other variables (e.g. 'KC*2', 'floor(value*MR)').")

    # Subplot grid
    parser.add_argument("--x_subplot", help="Dimension to map to subplot columns.")
    parser.add_argument("--y_subplot", help="Dimension to map to subplot rows.")

    # Processing
    parser.add_argument("--list_params", action="store_true",
                        help="List all available dimensions and JSON keys, then exit.")

    # Display / output
    parser.add_argument("--output_dir",   default="plots",
                        help="Directory to save output plots (default: 'plots').")
    parser.add_argument("--preview",      action="store_true",
                        help="Show the first plot in a window.")
    parser.add_argument("--global_scale", action="store_true",
                        help="Use the same color scale (vmin/vmax) across all plots.")
    parser.add_argument("--value_label",  help="Custom label for the color bar. Defaults to --value.")
    parser.add_argument("--cmap",         default="viridis",
                        help="Matplotlib colormap name (default: 'viridis').")
    parser.add_argument("--annotate",     action="store_true",
                        help="Annotate each heatmap cell with its numeric value.")
    parser.add_argument("--int_annotate", action="store_true",
                        help="Annotate each heatmap cell with its integer value.")
    parser.add_argument("--one_decimal", action="store_true",
                        help="Annotate each heatmap cell with one decimal place.")
    parser.add_argument("--tens_scale", action="store_true",
                        help="Scale values to be displayed in tens (XX.Y) by reducing the exponent by 1.")
    parser.add_argument("--fmt",          default=".2f",
                        help="Python format string for cell annotations (default: '.2f').")
    parser.add_argument("--x_ticks_from_data", action="store_true",
                        help="(Accepted for compatibility; heatmap ticks are always from data.)")

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
    if not args.x:
        print("Error: --x is required.")
        sys.exit(1)
    if not args.y:
        print("Error: --y is required.")
        sys.exit(1)
    if not args.value and not args.formula:
        print("Error: Either --value or --formula is required.")
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
        print(f"Global color scale: vmin={global_vmin:.4g}, vmax={global_vmax:.4g}")

    os.makedirs(args.output_dir, exist_ok=True)

    value_label   = args.value_label if args.value_label else (args.formula if args.formula else args.value)
    base_filename_key = args.formula if args.formula else args.value
    base_filename = f"heatmap_{sanitize_filename(base_filename_key)}"

    print(f"Generating plot: {base_filename}...")

    # ---- Subplot grid (only when explicitly requested) ----
    row_vals = sorted(df[args.y_subplot].unique()) if args.y_subplot else [None]
    col_vals = sorted(df[args.x_subplot].unique()) if args.x_subplot else [None]
    nrows = len(row_vals)
    ncols = len(col_vals)

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols,
        figsize=(8 * ncols + 2, 6 * nrows + 1),
        squeeze=False
    )
    fig.suptitle(
        f"{value_label}  |  rows={args.y}  cols={args.x}\n({base_filename})",
        fontsize=14
    )

    im_list = []

    for i, r_val in enumerate(row_vals):
        for j, c_val in enumerate(col_vals):
            ax = axes[i, j]

            sub = df.copy()
            if args.y_subplot:
                sub = sub[sub[args.y_subplot] == r_val]
            if args.x_subplot:
                sub = sub[sub[args.x_subplot] == c_val]

            if sub.empty:
                ax.axis('off')
                continue

            # Pivot: rows = y-dim, cols = x-dim, values = metric
            # aggfunc='mean' handles the case where other dims make duplicates
            try:
                pivot = sub.pivot_table(
                    index=args.y, columns=args.x,
                    values=value_col, aggfunc='mean'
                )
                # Reindex to ALL unique x/y values so fully-empty rows/cols aren't dropped
                all_x = sorted(sub[args.x].dropna().unique())
                all_y = sorted(sub[args.y].dropna().unique())
                pivot = pivot.reindex(index=all_y, columns=all_x)
            except Exception as e:
                print(f"  Warning: pivot failed for subplot ({r_val},{c_val}): {e}")
                ax.axis('off')
                continue

            # Sort axes for readability
            pivot = pivot.sort_index(ascending=False)   # rows: high→low
            pivot = pivot.sort_index(axis=1)            # cols: low→high

            # Mask NaN cells (no data / empty JSON) → shown as grey "N/A"
            data = pivot.values.copy()
            missing_mask = np.isnan(data)
            masked_data = np.ma.masked_where(missing_mask, data)

            cmap_obj = plt.get_cmap(args.cmap).copy()
            cmap_obj.set_bad(color='lightgrey')

            # vmin/vmax only over valid data
            valid_vals = data[~missing_mask]
            if args.global_scale:
                vmin, vmax = global_vmin, global_vmax
            else:
                vmin = float(valid_vals.min()) if len(valid_vals) else 0
                vmax = float(valid_vals.max()) if len(valid_vals) else 1

            # Compute a shared scale factor from the max value (e.g. 2.0e7 → 1e7)
            abs_max = max(abs(vmin), abs(vmax)) if vmax != vmin else abs(vmax)
            # If int_annotate is on, force scale to 1 (x10^0)
            if args.int_annotate:
                exp = 0
                scale = 1
            elif abs_max > 0:
                exp = int(np.floor(np.log10(abs_max)))
                if args.tens_scale:
                    exp -= 1
                scale = 10 ** exp
            else:
                exp, scale = 0, 1
            scale_label_suffix = f" (×10^{exp})" if exp != 0 else ""

            im = ax.imshow(
                masked_data / scale,
                aspect='equal',
                cmap=cmap_obj,
                vmin=vmin / scale,
                vmax=vmax / scale,
                origin='upper'
            )
            im_list.append((im, scale, exp))

            # Axis ticks
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([int(v) for v in pivot.columns], rotation=45, ha='right', fontsize=12)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([int(v) for v in pivot.index], fontsize=12)
            ax.set_xlabel(args.x, fontsize=14)
            ax.set_ylabel(args.y, fontsize=14)

            # Subplot title
            title_parts = []
            if args.y_subplot:
                title_parts.append(f"{args.y_subplot}={r_val}")
            if args.x_subplot:
                title_parts.append(f"{args.x_subplot}={c_val}")
            ax.set_title(", ".join(title_parts), fontsize=14)

            # Cell annotations: scaled and rounded
            if args.annotate or args.int_annotate or args.one_decimal:
                for ri in range(pivot.shape[0]):
                    for ci in range(pivot.shape[1]):
                        cell_val = data[ri, ci]
                        if missing_mask[ri, ci]:
                            ax.text(ci, ri, "N/A",
                                    ha='center', va='center',
                                    fontsize=8, color='dimgray')
                        else:
                            scaled_val = cell_val / scale
                            norm_val = (cell_val - vmin) / (vmax - vmin) if vmax != vmin else 0.5
                            text_color = 'white' if norm_val < 0.5 else 'black'
                            
                            val_text = ""
                            if args.int_annotate:
                                val_text = f"{int(scaled_val)}"
                            elif args.one_decimal:
                                val_text = f"{scaled_val:.1f}"
                            else:
                                val_text = f"{scaled_val:.2f}" 

                            ax.text(ci, ri, val_text,
                                    ha='center', va='center',
                                    fontsize=8, color=text_color)

    # Shared colorbar on the right — use scale from last valid plot
    if im_list:
        last_im, last_scale, last_exp = im_list[-1]
        fig.subplots_adjust(right=0.88)
        cbar_ax = fig.add_axes([0.91, 0.1, 0.02, 0.8])
        cbar = fig.colorbar(last_im, cax=cbar_ax)
        cbar_lbl = value_label + (f" (×10^{last_exp})" if last_exp != 0 else "")
        cbar.set_label(cbar_lbl, fontsize=16)
        cbar.ax.tick_params(labelsize=16)

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

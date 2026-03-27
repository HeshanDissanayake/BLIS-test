#!/usr/bin/env python3
"""
filter_heatmap.py

Visualizes cascaded filters on a 2D heatmap.

Arguments:
  --x, --y        Dimensions for the heatmap axes.
  --cascade       Define a filter cascade (list of formulas). 
                  Can be used multiple times to define independent cascades.
                  Example: --cascade "KC>64" "max(ipc)" --cascade "MC>100"
                  
                  LOGIC:
                  - Each --cascade defines a sequence of filters.
                  - Filters within a cascade are AND-ed sequentially (Level 1, Level 2...)
                  - Later cascades OVERWRITE the color of matching points.
                  
                  This allows layering different filter logic on the same map.

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
from matplotlib.patches import Patch

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def parse_folder_name(folder_name):
    match_underscore = re.match(r"^([a-zA-Z0-9_]+)_([a-zA-Z0-9\.]+)$", folder_name)
    if match_underscore:
        return match_underscore.group(1), match_underscore.group(2)
    match_concat = re.match(r"^([a-zA-Z]+)(\d+(?:\.\d+)?)$", folder_name)
    if match_concat:
        return match_concat.group(1), match_concat.group(2)
    return None, None


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

# ---------------------------------------------------------------------------
# Optimized Data Loading & Column Sanitization
# ---------------------------------------------------------------------------

def sanitize_column_name(col):
    return re.sub(r'[^a-zA-Z0-9_]', '_', col)


def load_data_as_df(root_dir):
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
            
            record = {}
            path_parts = rel_path.split(os.sep)
            for part in path_parts:
                if part == '.': continue
                k, v = parse_folder_name(part)
                if k:
                    try:
                        v = float(v) if '.' in v else int(v)
                    except: pass
                    record[k] = v
                    
            try:
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                
                flat_json = flatten_json(json_data)
                record.update(flat_json)
                record['category'] = 0
                data_records.append(record)
                
            except Exception:
                pass

    if not data_records:
        return pd.DataFrame(), {}
        
    df = pd.DataFrame(data_records)
    
    key_map = {}
    rename_map = {}
    
    for col in df.columns:
        safe_col = sanitize_column_name(col)
        rename_map[col] = safe_col
        key_map[col] = safe_col
        
    df = df.rename(columns=rename_map)
    return df, key_map


def prepare_formula(formula, key_map):
    safe_formula = formula
    sorted_keys = sorted(key_map.keys(), key=len, reverse=True)
    
    for original_key in sorted_keys:
        safe_key = key_map[original_key]
        if original_key == safe_key:
            continue
            
        if original_key in formula:
            esc_key = re.escape(original_key)
            pattern = r'(?<![a-zA-Z0-9_.-])' + esc_key + r'(?![a-zA-Z0-9_.-])'
            safe_formula = re.sub(pattern, safe_key, safe_formula)
            
    return safe_formula


def apply_cascade_vectorized_multi(df, cascades, key_map):
    """
    Applies multiple independent cascades sequentially.
    """
    if df.empty:
        return df
        
    start_category = 1
    
    for c_idx, cascade_filters in enumerate(cascades):
        # Reset mask for new cascade - all rows are candidates initially
        active_mask = pd.Series(True, index=df.index)
        
        for i, filter_str in enumerate(cascade_filters):
            level = i + 1
            current_category_val = start_category + i
            
            # Check for reduction
            match = re.match(r'^\s*(max|min)\s*\((.*)\)\s*$', filter_str, re.IGNORECASE)
            
            safe_expr = ""
            is_reduction = False
            reduction_mode = ""
            
            if match:
                is_reduction = True
                reduction_mode = match.group(1).lower()
                raw_expr = match.group(2)
                safe_expr = prepare_formula(raw_expr, key_map)
            else:
                safe_expr = prepare_formula(filter_str, key_map)
                
            current_subset = df[active_mask].copy()
            
            if current_subset.empty:
                break
                
            try:
                if is_reduction:
                    values = current_subset.eval(safe_expr)
                    
                    if reduction_mode == 'max':
                        target = values.max()
                    else:
                        target = values.min()
                    
                    if np.issubdtype(values.dtype, np.number):
                         new_matches = np.isclose(values, target, rtol=1e-9)
                    else:
                         new_matches = (values == target)
                         
                    subset_indices = current_subset.index[new_matches]
                    new_active_mask = pd.Series(False, index=df.index)
                    new_active_mask.loc[subset_indices] = True
                    active_mask = new_active_mask

                else:
                    matches = current_subset.eval(safe_expr)
                    subset_indices = current_subset.index[matches]
                    new_active_mask = pd.Series(False, index=df.index)
                    new_active_mask.loc[subset_indices] = True
                    active_mask = new_active_mask
    
                # Mark survivors
                df.loc[active_mask, 'category'] = current_category_val
    
            except Exception as e:
                print(f"Error evaluating filter '{filter_str}': {e}")
                break
        
        start_category += len(cascade_filters)
            
    return df


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filter and visualize cascaded data points (Optimized)."
    )
    parser.add_argument("--root",    required=True, help="Base directory.")
    parser.add_argument("--x",       required=True, help="X dimension.")
    parser.add_argument("--y",       required=True, help="Y dimension.")
    
    parser.add_argument("--cascade", action="append", nargs="+", dest="cascades",
                        help="Define a cascade. Example: --cascade 'KC>64' 'max(ipc)'")
    parser.add_argument("--group",   action="append", nargs="+", dest="groups",
                        help="Generate cascades by grouping a variable. Example: --group 'MR*NR' 'max(ipc)'")
    parser.add_argument("--filter",  action="append", dest="filters",
                        help="(Legacy) Add to the default cascade.")
                        
    parser.add_argument("--x_subplot", help="Subplot X.")
    parser.add_argument("--y_subplot", help="Subplot Y.")
    parser.add_argument("--output_dir", default="plots", help="Output dir.")
    parser.add_argument("--preview",    action="store_true", help="Show plot.")
    parser.add_argument("--list_params", action="store_true", help="List params.")
    return parser.parse_args()


def sanitize_filename(text):
    # Replace non-alphanum with _
    s = re.sub(r'[^a-zA-Z0-9]+', '_', text)
    s = s.strip('_')
    return s[:100]


def plot_cascade(df, cascades, key_map, args, output_suffix=""):
    """
    Plots the given set of cascades (filtered df) to a file.
    """
    safe_x = key_map.get(args.x, args.x)
    safe_y = key_map.get(args.y, args.y)
    safe_sx = key_map.get(args.x_subplot, args.x_subplot) if args.x_subplot else None
    safe_sy = key_map.get(args.y_subplot, args.y_subplot) if args.y_subplot else None
    
    # -------------------------------------------------------
    # Plotting
    # -------------------------------------------------------
    total_levels = sum(len(c) for c in cascades)
    if total_levels == 0:
        print("No levels to plot.")
        return

    # Colors
    cmap_base = plt.get_cmap('tab10') if total_levels <= 10 else plt.get_cmap('rainbow')
    colors = ['black'] 
    for i in range(total_levels):
        colors.append(cmap_base(i / max(1, total_levels - 1) if total_levels > 10 else i))
        
    custom_cmap = mcolors.ListedColormap(colors)
    bounds = np.arange(-0.5, total_levels + 1.5, 1)
    norm = mcolors.BoundaryNorm(bounds, custom_cmap.N)

    os.makedirs(args.output_dir, exist_ok=True)
    
    row_vals = sorted(df[safe_sy].unique()) if safe_sy else [None]
    col_vals = sorted(df[safe_sx].unique()) if safe_sx else [None]
    nrows = len(row_vals)
    ncols = len(col_vals)

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, 
        figsize=(6 * ncols + 4, 5 * nrows), 
        squeeze=False
    )
    
    title_parts = []
    for c in cascades:
        title_parts.append(" -> ".join([str(f) for f in c]))
    title_str = " | ".join(title_parts)
    if len(title_str) > 60: title_str = title_str[:60] + "..."
    
    fig.suptitle(f"Filter: {title_str}\n(y={args.y}, x={args.x})", fontsize=12)

    for i, r_val in enumerate(row_vals):
        for j, c_val in enumerate(col_vals):
            ax = axes[i, j]
            
            sub = df.copy()
            if safe_sy: sub = sub[sub[safe_sy] == r_val]
            if safe_sx: sub = sub[sub[safe_sx] == c_val]
            
            if sub.empty:
                ax.axis('off')
                continue

            try:
                # Pivot
                pivot = sub.pivot_table(
                    index=safe_y, columns=safe_x, values='category', aggfunc='max'
                )
                
                all_x = sorted(sub[safe_x].dropna().unique())
                all_y = sorted(sub[safe_y].dropna().unique())
                pivot = pivot.reindex(index=all_y, columns=all_x)
                
                pivot = pivot.sort_index(ascending=False)
                pivot = pivot.sort_index(axis=1)

                data_values = pivot.values
                masked_array = np.ma.masked_invalid(data_values)
                
                current_cmap = custom_cmap.copy()
                current_cmap.set_bad(color='lightgrey')
                
                im = ax.imshow(
                    masked_array, 
                    cmap=current_cmap, 
                    norm=norm,
                    origin='upper',
                    aspect='equal'
                )

                ax.set_xticks(range(len(pivot.columns)))
                ax.set_xticklabels([str(p) for p in pivot.columns], rotation=45, ha='right', fontsize=9)
                ax.set_yticks(range(len(pivot.index)))
                ax.set_yticklabels([str(p) for p in pivot.index], fontsize=9)
                ax.set_xlabel(args.x, fontsize=10)
                ax.set_ylabel(args.y, fontsize=10)
                
                ax.set_xticks(np.arange(len(pivot.columns)) - 0.5, minor=True)
                ax.set_yticks(np.arange(len(pivot.index)) - 0.5, minor=True)
                ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
                ax.tick_params(which="minor", bottom=False, left=False)

                if args.y_subplot or args.x_subplot:
                    lbls = []
                    if args.y_subplot: lbls.append(f"{args.y_subplot}={r_val}")
                    if args.x_subplot: lbls.append(f"{args.x_subplot}={c_val}")
                    ax.set_title(", ".join(lbls), fontsize=10)

            except Exception as e:
                print(f"Error plotting: {e}")
                ax.axis('off')

    # Legend
    legend_elements = [
        Patch(facecolor='lightgrey', edgecolor='gray', label='No Data'),
        Patch(facecolor='black', edgecolor='gray', label='Unmatched')
    ]
    
    current_color_idx = 1
    for c_idx, cascade in enumerate(cascades):
        prefix = f"C{c_idx+1}" if len(cascades) > 1 else ""
        
        for l_idx, finfo in enumerate(cascade):
            color = colors[current_color_idx]
            lbl = finfo[:20] + "..." if len(finfo) > 20 else finfo
            label_text = f"{prefix} L{l_idx+1}: {lbl}" if prefix else f"Level {l_idx+1}: {lbl}"
            legend_elements.append(
                Patch(facecolor=color, edgecolor='gray', label=label_text)
            )
            current_color_idx += 1
        
    fig.legend(handles=legend_elements, loc='center right', title="Filters")
    plt.subplots_adjust(right=0.82) 

    safe_name = f"heatmap_{sanitize_filename(output_suffix)}"
    png_path = os.path.join(args.output_dir, f"{safe_name}.png")
    
    try:
        plt.savefig(png_path, dpi=150)
        print(f"Saved: {png_path}")
    except Exception as e:
        print(f"Error saving {png_path}: {e}")
    
    if args.preview:
        plt.show()
    plt.close(fig)


def main():
    args = parse_args()

    if args.list_params:
        df, key_map = load_data_as_df(args.root)
        if not df.empty:
            print("Available Keys (Original -> Safe):")
            for k, stored_k in sorted(key_map.items()):
                print(f"  {k:<40} -> {stored_k}")
        return

    if not args.cascades and not args.filters and not args.groups:
        print("Error: At least one --cascade, --filter or --group is required.")
        sys.exit(1)

    # 1. Load Data
    df, key_map = load_data_as_df(args.root)
    if df.empty:
        print("No data found.")
        sys.exit(1)

    safe_x = key_map.get(args.x, args.x)
    safe_y = key_map.get(args.y, args.y)
    safe_sx = key_map.get(args.x_subplot, args.x_subplot) if args.x_subplot else None
    safe_sy = key_map.get(args.y_subplot, args.y_subplot) if args.y_subplot else None

    # Type coercion
    for col in df.columns:
        if col == 'category': continue
        try:
             df[col] = pd.to_numeric(df[col], errors='coerce')
        except: pass

    # Convert axis/group columns to strings if unsortable
    for col in [safe_x, safe_y, safe_sx, safe_sy]:
        if col and col in df.columns:
            has_iterables = df[col].apply(lambda x: isinstance(x, (list, tuple))).any()
            if has_iterables:
                 df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, tuple)) else x)

    # Prepare list of cascades
    all_cascades = []
    if args.filters:
        all_cascades.append(args.filters)
    if args.cascades:
        all_cascades.extend(args.cascades)
    
    if args.groups:
        for grp in args.groups:
            if not grp: continue
            raw_expr = grp[0]
            others = grp[1:]
            
            safe_expr = prepare_formula(raw_expr, key_map)
            try:
                vals = df.eval(safe_expr)
                unique_vals = sorted(vals.dropna().unique())
                print(f"Group '{raw_expr}' found {len(unique_vals)} unique values: {unique_vals}")
                
                for val in unique_vals:
                    cond = f"({raw_expr}) == {repr(val)}"
                    new_cascade = [cond] + others
                    all_cascades.append(new_cascade)
            except Exception as e:
                print(f"Error processing group '{raw_expr}': {e}")
        
    print(f"Loaded {len(df)} records. Applying {len(all_cascades)} cascades...")

    # ----------------------------------------------------
    # BATCH CASCADE PROCESSING
    # We produce one file per cascade provided.
    # ----------------------------------------------------
    
    # Process each cascade independently
    for i, cascade in enumerate(all_cascades):
        print(f"\nProcessing Cascade {i+1}/{len(all_cascades)}: {cascade}")
        
        # Fresh copy of df
        df_c = df.copy()
        df_c['category'] = 0
        
        # Apply strict single cascade logic
        # We pass it as a list of ONE cascade to our vectorized function
        # But wait, our function supports list of cascades.
        
        # Let's use the function passing just [cascade]
        df_c = apply_cascade_vectorized_multi(df_c, [cascade], key_map)
        
        # Output filename based on first filter text
        # If there are multiple filters, start with first
        first_filter = cascade[0] if cascade else f"cascade_{i}"
        
        plot_cascade(df_c, [cascade], key_map, args, output_suffix=f"{first_filter}")

    # -----------------------------------------------------------------------
    # END BATCH
    # -----------------------------------------------------------------------
    # The following code block was the old "combined" logic, which we effectively replaced above.
    # We remove it to follow the user instruction "output file per cascade".
    pass

if __name__ == "__main__":
    main()

"""MR/NR heatmap generator.

Set `MR_LIST`, `NR_LIST`, and update `compute_value()` to match your model.
The script evaluates all (MR, NR) pairs and plots a heatmap with:
  - MR on x-axis
  - NR on y-axis
"""

from __future__ import annotations

import json
import os
import re
from typing import Callable

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from math import floor, ceil

SL1 = 32 *1024
CL1 = 16
WL1 = 8
NL1 = SL1 // (CL1 * WL1)
S_data = 8

# --- Configure these lists directly in code ---
MR_LIST = [2, 4, 6, 8, 10, 12, 14, 16, 18,20,22,24,26,28,30,32]#,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64]
NR_LIST = [2, 4, 6, 8, 10, 12, 14, 16, 18,20,22,24,26,28,30,32]#,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64]


OUTPUT_PNG = "mr_nr_heatmap.png"
OUTPUT_MASKED_DATA_PNG = "mr_nr_masked_data_heatmap.png"
DATA_ROOT_DIR = "/home/heshds/working_dir/BLIS-test/Experimants/spike-normal/experiment-34/analysed_data"
DATA_METRIC_PATH = "l1-i_dcaches.demand_fetches.total"
CELL_TEXT_FONTSIZE = 4
HIGHLIGHT_MODE_FORMULA = "max"   # "min", "max", or "none"
HIGHLIGHT_MODE_MASKED = "min"    # "min", "max", or "none"
HIGHLIGHT_BORDER_COLOR = "red"
HIGHLIGHT_BORDER_WIDTH = 2.0


def compute_value(selected_pairs: list[tuple[int, int]]) -> list[float]:
    """Compute values for all filtered (MR, NR) pairs.

    Put all per-pair computation logic here.
    The returned list order must match selected_pairs.
    """
 

    max_area = max(mr * nr for mr, nr in selected_pairs)



    
    WA = []
    KC = []
    WB = []

    tile_area = []
    cache_utilization = []
    score = []

    for mr,nr in selected_pairs:
        wa = (WL1 * mr) / (mr + nr)
        kc = (max(floor(wa), 1)/mr) * ((NL1*CL1)/S_data)
        wb = nr*kc*(S_data/(CL1*NL1))
        wc = (mr*nr*S_data)/(NL1*CL1)

        cache_util = (wa+wb+wc)/WL1
        tile_area_score = (mr * nr) / max_area

        sc = (max(0, 1-cache_util) +  tile_area_score )
        
        WA.append(wa)
        KC.append(floor(kc))
        WB.append(wb)
        cache_utilization.append(cache_util)

        

    max_kc = max(KC)
    for i in range(len(selected_pairs)):
        mr, nr = selected_pairs[i]
        tile_area_score = (mr * nr) / max_area
        tile_reuse_score = (KC[i] / max_kc)*tile_area_score

        sc = max(0, 1-cache_utilization[i]) + 0.51 * tile_reuse_score
        score.append(sc) 
    print(len(score), len(selected_pairs))
    return score


def filter_equation(mr: int, nr: int) -> bool:
    """Filter condition for selecting (MR, NR) pairs.

    Edit this equation as needed.
    """
    return ceil(( mr + nr + (mr * nr))/32) == 6


def flatten_json(y: dict) -> dict:
    """Flatten nested JSON keys using dot notation."""
    out: dict = {}

    def _flatten(x, name=""):
        if isinstance(x, dict):
            for a in x:
                _flatten(x[a], name + a + ".")
        else:
            out[name[:-1]] = x

    _flatten(y)
    return out


def load_metric_by_pair(root_dir: str, metric_path: str) -> dict[tuple[int, int], list[float]]:
    """Load metric values grouped by (MR, NR) from avg.json files in root_dir."""
    by_pair: dict[tuple[int, int], list[float]] = {}

    if not os.path.exists(root_dir):
        return by_pair

    for dirpath, _, filenames in os.walk(root_dir):
        if "avg.json" not in filenames:
            continue

        mr = None
        nr = None
        for part in dirpath.split(os.sep):
            m_mr = re.match(r"^MR(\d+)$", part)
            m_nr = re.match(r"^NR(\d+)$", part)
            if m_mr:
                mr = int(m_mr.group(1))
            if m_nr:
                nr = int(m_nr.group(1))

        if mr is None or nr is None:
            continue

        json_path = os.path.join(dirpath, "avg.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            flat = flatten_json(raw)
            if metric_path not in flat:
                continue
            value = float(flat[metric_path])
            by_pair.setdefault((mr, nr), []).append(value)
        except Exception:
            continue

    return by_pair


def build_masked_matrix_from_data(
    mr_list: list[int],
    nr_list: list[int],
    filter_fn: Callable[[int, int], bool],
    metric_by_pair: dict[tuple[int, int], list[float]],
) -> np.ndarray:
    """Build matrix from filesystem data for only filter-selected cells.

    Non-filtered cells or missing-data cells are NaN (masked in plot).
    """
    values = np.full((len(nr_list), len(mr_list)), np.nan, dtype=float)

    for y, nr in enumerate(nr_list):
        for x, mr in enumerate(mr_list):
            if not filter_fn(mr, nr):
                continue
            samples = metric_by_pair.get((mr, nr))
            if not samples:
                continue
            values[y, x] = float(np.mean(samples))

    return values

def get_filtered_combinations(
    mr_list: list[int],
    nr_list: list[int],
    filter_fn: Callable[[int, int], bool],
) -> list[tuple[int, int]]:
    """Return selected (MR, NR) combinations based on filter_fn."""
    selected: list[tuple[int, int]] = []
    for nr in nr_list:
        for mr in mr_list:
            if filter_fn(mr, nr):
                selected.append((mr, nr))
    return selected


def build_matrix_from_filtered_values(
    mr_list: list[int],
    nr_list: list[int],
    selected_pairs: list[tuple[int, int]],
    selected_values: list[float],
) -> np.ndarray:
    """Build matrix where non-selected cells are 0.

    selected_pairs and selected_values must have same length and order.
    """
    if len(selected_pairs) != len(selected_values):
        raise ValueError("selected_pairs and selected_values must have the same length")

    values = np.zeros((len(nr_list), len(mr_list)), dtype=float)
    mr_to_x = {mr: x for x, mr in enumerate(mr_list)}
    nr_to_y = {nr: y for y, nr in enumerate(nr_list)}

    for (mr, nr), val in zip(selected_pairs, selected_values):
        if mr not in mr_to_x or nr not in nr_to_y:
            continue
        x = mr_to_x[mr]
        y = nr_to_y[nr]
        values[y, x] = val

    return values


def _pick_target_mask(values: np.ndarray, valid_mask: np.ndarray, mode: str) -> np.ndarray:
    """Return mask of target cells to highlight for mode in {min, max, none}."""
    mode = mode.lower().strip()
    if mode == "none" or not np.any(valid_mask):
        return np.zeros_like(values, dtype=bool)

    valid_values = values[valid_mask]
    target = np.min(valid_values) if mode == "min" else np.max(valid_values)
    return valid_mask & np.isclose(values, target, rtol=1e-12, atol=1e-12)


def plot_heatmap(mr_list: list[int], nr_list: list[int], values: np.ndarray, output_png: str) -> None:
    """Plot heatmap with MR on x-axis and NR on y-axis, then save as PNG."""
    fig, ax = plt.subplots(figsize=(8, 5))

    img = ax.imshow(values, cmap="viridis", origin="lower", aspect="auto")

    def _auto_text_color(v: float) -> str:
        rgba = img.cmap(img.norm(v))
        r, g, b = rgba[:3]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "black" if luminance > 0.6 else "white"

    # Axes ticks/labels
    ax.set_xticks(np.arange(len(mr_list)))
    ax.set_yticks(np.arange(len(nr_list)))
    ax.set_xticklabels(mr_list)
    ax.set_yticklabels(nr_list)
    ax.set_xlabel("MR")
    ax.set_ylabel("NR")
    ax.set_title("Heatmap of formula values for (MR, NR)")

    # Optional: annotate cells with values
    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            if values[y, x] == 0:
                continue
            ax.text(
                x,
                y,
                f"{values[y, x]:.2f}",
                ha="center",
                va="center",
                color=_auto_text_color(float(values[y, x])),
                fontsize=CELL_TEXT_FONTSIZE,
            )

    nonzero_mask = values != 0
    target_mask = _pick_target_mask(values, nonzero_mask, HIGHLIGHT_MODE_FORMULA)
    if np.any(target_mask):
        for y, x in np.argwhere(target_mask):
            ax.add_patch(
                Rectangle(
                    (x - 0.5, y - 0.5),
                    1,
                    1,
                    fill=False,
                    edgecolor=HIGHLIGHT_BORDER_COLOR,
                    linewidth=HIGHLIGHT_BORDER_WIDTH,
                    zorder=5,
                )
            )

    cbar = plt.colorbar(img, ax=ax)
    cbar.set_label("Value")

    plt.tight_layout()
    fig.savefig(output_png, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_masked_data_heatmap(
    mr_list: list[int],
    nr_list: list[int],
    values: np.ndarray,
    output_png: str,
    title: str,
) -> None:
    """Plot masked heatmap where NaN cells are hidden."""
    fig, ax = plt.subplots(figsize=(8, 5))

    masked_values = np.ma.masked_invalid(values)
    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color="white", alpha=0.0)
    img = ax.imshow(masked_values, cmap=cmap, origin="lower", aspect="auto")

    def _auto_text_color(v: float) -> str:
        rgba = img.cmap(img.norm(v))
        r, g, b = rgba[:3]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "black" if luminance > 0.6 else "white"

    ax.set_xticks(np.arange(len(mr_list)))
    ax.set_yticks(np.arange(len(nr_list)))
    ax.set_xticklabels(mr_list)
    ax.set_yticklabels(nr_list)
    ax.set_xlabel("MR")
    ax.set_ylabel("NR")
    ax.set_title(title)

    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            if np.isnan(values[y, x]):
                continue
            ax.text(
                x,
                y,
                f"{values[y, x]:.3f}",
                ha="center",
                va="center",
                color=_auto_text_color(float(values[y, x])),
                fontsize=CELL_TEXT_FONTSIZE,
            )

    finite_mask = np.isfinite(values)
    target_mask = _pick_target_mask(values, finite_mask, HIGHLIGHT_MODE_MASKED)
    if np.any(target_mask):
        for y, x in np.argwhere(target_mask):
            ax.add_patch(
                Rectangle(
                    (x - 0.5, y - 0.5),
                    1,
                    1,
                    fill=False,
                    edgecolor=HIGHLIGHT_BORDER_COLOR,
                    linewidth=HIGHLIGHT_BORDER_WIDTH,
                    zorder=5,
                )
            )

    cbar = plt.colorbar(img, ax=ax)
    cbar.set_label(DATA_METRIC_PATH)

    plt.tight_layout()
    fig.savefig(output_png, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # 1) Get filtered (MR, NR) combinations
    selected_pairs = get_filtered_combinations(MR_LIST, NR_LIST, filter_equation)

    # 2) Do your computation only for selected pairs (replace with your own values)
    selected_values = compute_value(selected_pairs)

    # 3) Build heatmap matrix (all non-selected cells remain 0)
    values = build_matrix_from_filtered_values(MR_LIST, NR_LIST, selected_pairs, selected_values)
    plot_heatmap(MR_LIST, NR_LIST, values, OUTPUT_PNG)

    # 4) Build masked heatmap from analysed_data using same filter equation
    metric_by_pair = load_metric_by_pair(DATA_ROOT_DIR, DATA_METRIC_PATH)
    masked_values = build_masked_matrix_from_data(MR_LIST, NR_LIST, filter_equation, metric_by_pair)
    plot_masked_data_heatmap(
        MR_LIST,
        NR_LIST,
        masked_values,
        OUTPUT_MASKED_DATA_PNG,
        "Masked heatmap from analysed_data (filtered MR/NR)",
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Derive per-config timing constants from:
    cycles = t_c*(inst - r - w) + t_rh*(r - rmisses) + t_rm*rmisses + t_w*w

Where:
    inst - r - w   = compute (non-memory) instructions
    r - rmisses    = read hits
    rmisses        = read misses
    w              = all writes (hits+misses merged — they are collinear)

Uses non-negative least squares (nnls) — all constants guaranteed >= 0.
"""

import numpy as np
import pandas as pd
from scipy.optimize import nnls

# ── Load ────────────────────────────────────────────────────────────────────
df = pd.read_csv("data.csv")
df.columns = [c.strip() for c in df.columns]

print("Columns:", list(df.columns))
print(f"Data points (KC values): {len(df)}\n")

configs = [4, 8, 16]

results = {}
for cfg in configs:
    cycles  = df[f"cycles_{cfg}"].values.astype(float)
    insts   = df[f"insts_{cfg}"].values.astype(float)
    r       = df[f"r_{cfg}"].values.astype(float)
    w       = df[f"w_{cfg}"].values.astype(float)
    rmisses = df[f"rmisses_{cfg}"].values.astype(float)

    compute = insts - r - w      # non-memory instructions
    r_hits  = r - rmisses        # read hits

    # Build matrix A: each row is [compute, r_hits, rmisses, w]
    A = np.column_stack([compute, r_hits, rmisses, w])

    # Solve: A @ [t_c, t_rh, t_rm, t_w]^T ≈ cycles
    coeffs, _ = nnls(A, cycles)
    t_c, t_rh, t_rm, t_w = coeffs

    predicted = A @ coeffs
    rel_err   = np.abs((predicted - cycles) / cycles) * 100

    results[cfg] = {
        "t_c": t_c, "t_rh": t_rh, "t_rm": t_rm, "t_w": t_w,
        "mean_rel_err_%": rel_err.mean(),
        "max_rel_err_%":  rel_err.max(),
    }

    print(f"Config MR/NR = {cfg}")
    print(f"  t_c  (cycles / compute instr) = {t_c:.6f}")
    print(f"  t_rh (cycles / read hit)      = {t_rh:.6f}")
    print(f"  t_rm (cycles / read miss)     = {t_rm:.2f}")
    print(f"  t_w  (cycles / write)         = {t_w:.6f}")
    print(f"  Mean relative error           = {rel_err.mean():.2f}%")
    print(f"  Max  relative error           = {rel_err.max():.2f}%")
    print()

# ── Summary table ────────────────────────────────────────────────────────────
w = 10
print("─" * 52)
print(f"{'Config':>8} {'t_c':>{w}} {'t_rh':>{w}} {'t_rm':>{w}} {'t_w':>{w}} {'MeanErr%':>{w}}")
print("─" * 52)
for cfg, r in results.items():
    print(f"{cfg:>8} {r['t_c']:>{w}.4f} {r['t_rh']:>{w}.4f} {r['t_rm']:>{w}.2f} "
          f"{r['t_w']:>{w}.4f} {r['mean_rel_err_%']:>{w}.2f}")
print("─" * 52)

# ── Save ─────────────────────────────────────────────────────────────────────
out = pd.DataFrame(results).T
out.index.name = "config"
out.to_csv("constants.csv", float_format="%.6f")
print("\nSaved to constants.csv")

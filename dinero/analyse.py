#!/usr/bin/env python3

import subprocess
import re
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("trace")
PYTHON_EXTRACT = "extract_missrate.py"

DINERO_FLAGS = [
    "-l1-isize", "8k",
    "-l1-ibsize", "16",
    "-l1-iassoc", "2",
    "-l1-irepl", "l",
    "-l1-ifetch", "d",
    "-l1-dsize", "32k",
    "-l1-dbsize", "16",
    "-l1-dassoc", "8",
    "-l1-drepl", "l",
    "-l1-dfetch", "d",
    "-l1-dwalloc", "a",
    "-l1-dwback", "a",
    "-flushcount", "10k",
    "-stat-idcombine",
    "-informat", "D",
]

# data[reg][N][cache] = miss_rate
data = defaultdict(lambda: defaultdict(dict))


def extract_n(logfile: Path) -> int:
    m = re.search(r"N(\d+)\.log", logfile.name)
    return int(m.group(1))


def run_dinero(logfile: Path) -> str:
    """Run dineroIV on a log file and return miss rate as string."""
    with logfile.open("rb") as f:
        dinero = subprocess.Popen(
            ["dineroIV", *DINERO_FLAGS],
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        extract = subprocess.Popen(
            ["python3", PYTHON_EXTRACT],
            stdin=dinero.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        dinero.stdout.close()
        out, err = extract.communicate()

        if extract.returncode != 0:
            raise RuntimeError(f"extract_missrate.py failed on {logfile}\n{err}")

        return out.strip()


# -------- Discover cache configs --------
cache_configs = sorted(
    [d.name for d in BASE_DIR.iterdir() if d.is_dir()]
)

for cache in cache_configs:
    cache_dir = BASE_DIR / cache
    print(f"Processing cache config: {cache}")

    # -------- Discover & sort reg configs numerically --------
    reg_cfgs = sorted(
        [d.name for d in cache_dir.iterdir() if d.is_dir()],
        key=lambda x: int(x.split("x")[0]),
    )

    for reg in reg_cfgs:
        reg_dir = cache_dir / reg

        # -------- Discover & sort N files numerically --------
        n_logs = sorted(
            reg_dir.glob("N*.log"),
            key=lambda p: extract_n(p),
        )

        for log in n_logs:
            n = extract_n(log)

            print(f"  {cache} | {reg} | N{n}")

            miss_rate = run_dinero(log)
            data[reg][n][cache] = miss_rate


# -------- Write CSVs (one per reg config) --------
for reg, n_dict in data.items():
    csv_path = Path(f"{reg}.csv")
    n_values = sorted(n_dict.keys())

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["N"] + cache_configs)

        for n in n_values:
            row = [f"N{n}"]
            for cache in cache_configs:
                row.append(n_dict[n].get(cache, "NA"))
            writer.writerow(row)

    print(f"Wrote {csv_path}")

print("All done.")

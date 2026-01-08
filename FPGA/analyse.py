import re
import csv
import sys
from collections import defaultdict

CLOCK_MHZ = 50.0


# ---------------- ARGUMENTS ----------------
if len(sys.argv) < 2:
    print("Usage: python parse_gemm_log.py <logfile> [MC NC KC]")
    sys.exit(1)

LOG_FILE = sys.argv[1]

# Column order inside CSV header (configurable)
if len(sys.argv) > 2:
    COLUMN_ORDER = sys.argv[2:]
else:
    COLUMN_ORDER = ["MC", "NC", "KC"]

OUTPUT_PREFIX = ""
# ------------------------------------------


benchmark_re = re.compile(
    r"benchmark:\s(?P<bin>gemm_blis_(?P<MR>\d+)x(?P<NR>\d+))\s+"
    r"MC_(?P<MC>\d+)_KC_(?P<KC>\d+)_NC_(?P<NC>\d+)"
)

data = defaultdict(lambda: defaultdict(dict))
# data[bin][(MC,NC,KC)][N] = cycles

current_bin = None
current_cfg = None

with open(LOG_FILE, "r", errors="ignore") as f:
    for line in f:
        line = line.strip()

        m = benchmark_re.search(line)
        print(m)
        if m:
            current_bin = m.group("bin")
            cfg_map = {
                "MC": int(m.group("MC")),
                "NC": int(m.group("NC")),
                "KC": int(m.group("KC")),
            }
            current_cfg = tuple(cfg_map[k] for k in COLUMN_ORDER)
            continue

        if current_bin and line.startswith("N,"):
            parts = line.split(",")
            N = int(parts[1])
            cycles = int(parts[3])

            # FLOPs = 2 * N^3
            flops = 2.0 * (N ** 3)

            # MFLOPS = (FLOPs / cycles) * (clock MHz)
            if current_bin == "gemm_blis_8x8":
                mflops = (flops / cycles) * CLOCK_MHZ * 1.4225
            elif current_bin == "gemm_blis_16x16":
                mflops = (flops / cycles) * CLOCK_MHZ * 1.3616
            else:
                mflops = (flops / cycles) * CLOCK_MHZ
            
            data[current_bin][current_cfg][N] = round(mflops, 3)


# ---------------- WRITE CSVs ----------------
for bin_name, cfgs in data.items():
   
    all_N = sorted({N for cfg in cfgs.values() for N in cfg})
    ordered_cfgs = sorted(cfgs.keys())

    headers = ["N"]
    for cfg in ordered_cfgs:
        headers.append(
            "_".join(f"{k}{v}" for k, v in zip(COLUMN_ORDER, cfg))
        )

    out_file = f"{OUTPUT_PREFIX}{bin_name}.csv"
    with open(out_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for N in all_N:
            row = [N]
            for cfg in ordered_cfgs:
                row.append(cfgs[cfg].get(N, ""))
            writer.writerow(row)

    print(f"Written {out_file}")

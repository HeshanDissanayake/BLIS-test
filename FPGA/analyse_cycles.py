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

data_cycles = defaultdict(lambda: defaultdict(dict))
data_instret = defaultdict(lambda: defaultdict(dict))
# data_cycles[bin][(MC,NC,KC)][N] = mflops_based_on_cycles
# data_instret[bin][(MC,NC,KC)][N] = mflops_based_on_instret

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
            instret = int(parts[5]) if len(parts) > 5 else None

    
            
            data_cycles[current_bin][current_cfg][N] = cycles
            
            if instret is not None:
                mflops_instret = (flops / instret) * clock_factor
                data_instret[current_bin][current_cfg][N] = round(mflops_instret, 3)


# ---------------- WRITE CSVs ----------------
for bin_name in set(data_cycles.keys()) | set(data_instret.keys()):
    cfgs_cycles = data_cycles.get(bin_name, {})
    cfgs_instret = data_instret.get(bin_name, {})
    
    all_N = sorted({N for cfg in cfgs_cycles.values() for N in cfg} | 
                   {N for cfg in cfgs_instret.values() for N in cfg})
    ordered_cfgs = sorted(set(cfgs_cycles.keys()) | set(cfgs_instret.keys()))

    headers = ["N"]
    for cfg in ordered_cfgs:
        headers.append(
            "_".join(f"{k}{v}" for k, v in zip(COLUMN_ORDER, cfg))
        )

    out_file = f"{OUTPUT_PREFIX}{bin_name}.csv"
    with open(out_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        
        # Write cycles data
        writer.writerow(["Cycles MFLOPS"])
        writer.writerow(headers)
        for N in all_N:
            row = [N]
            for cfg in ordered_cfgs:
                row.append(cfgs_cycles.get(cfg, {}).get(N, ""))
            writer.writerow(row)
        
        # Add spacing
        writer.writerow([])
        writer.writerow([])
        writer.writerow([])
        
        # Write instret data
        writer.writerow(["Instret MFLOPS"])
        writer.writerow(headers)
        for N in all_N:
            row = [N]
            for cfg in ordered_cfgs:
                row.append(cfgs_instret.get(cfg, {}).get(N, ""))
            writer.writerow(row)

    print(f"Written {out_file}")

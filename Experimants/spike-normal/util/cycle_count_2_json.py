#!/usr/bin/env python3
import argparse
import os
import json
import re

def parse_cycle_log(filepath):
    """
    Parses lines like: N,128,cycles,7935353,instret,7935353
    Returns dict: {128: 7935353, 160: 15205622, ...}
    """
    data = {}
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            # Match: N,<size>,cycles,<count>,instret,<instret>
            m = re.match(r'^N,(\d+),cycles,(\d+),instret,(\d+)$', line)
            if m:
                n = int(m.group(1))
                cycles = int(m.group(2))
                data[n] = cycles
    return data

def main():
    parser = argparse.ArgumentParser(description="Parse cycle count log and write to JSON")
    parser.add_argument("--MC", required=True, help="MC value")
    parser.add_argument("--NC", required=True, help="NC value")
    parser.add_argument("--KC", required=True, help="KC value")
    parser.add_argument("--MR", required=True, help="MR value")
    parser.add_argument("--EXP_DIR", required=True, help="Experiment directory path")

    args = parser.parse_args()

    # Input: cycle count log file
    log_path = os.path.join(args.EXP_DIR, "memtraces", f"MC{args.MC}", f"KC{args.KC}", f"NC{args.NC}", f"MR{args.MR}", f"cycle_count_MR{args.MR}")

    if not os.path.isfile(log_path):
        print(f"Error: Log file not found: {log_path}")
        return

    data = parse_cycle_log(log_path)

    if not data:
        print(f"Warning: No cycle data found in {log_path}")
        return

    # Output: JSON file
    out_dir = os.path.join(args.EXP_DIR, "cycles", f"MC{args.MC}", f"KC{args.KC}", f"NC{args.NC}", f"MR{args.MR}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cycle.json")

    with open(out_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Written {len(data)} entries: {out_path}")

if __name__ == "__main__":
    main()

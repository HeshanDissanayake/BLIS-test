#!/usr/bin/env python3
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Merge multiple CSVs on a common key column")
parser.add_argument("csvs", nargs="+", help="CSV files to merge")
parser.add_argument("--on", default="KC", help="Column to join on (default: KC)")
parser.add_argument("--output", "-o", required=True, help="Output CSV file")
args = parser.parse_args()

df = None
for path in args.csvs:
    cur = pd.read_csv(path)
    df = cur if df is None else df.merge(cur, on=args.on)

df.to_csv(args.output, index=False)
print(f"Saved {args.output}")

#!/usr/bin/env python3
import sys
import csv
import re



# Regex to match 'Demand miss rate' and the first float value
pattern = re.compile(r"Demand miss rate\s+([0-9.]+)")

miss_rate = None

# Read stdin line by line (streaming-friendly)
for line in sys.stdin:
    match = pattern.search(line)
    if match:
        miss_rate = match.group(1)
        break

if miss_rate is None:
    print("NA")
    sys.exit(1)

print(miss_rate)
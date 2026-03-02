#!/usr/bin/env python3
import sys
import re
import json

def parse_line(line):
    # Split by whitespace, but be careful about the label which might contain spaces
    # Actually, Dinero output seems to be fixed columns, but let's try regex based on the specific labels we know.
    parts = line.strip().split()
    return parts

def main():
    data = {}
    
    # regex patterns for lines we care about
    # "Demand Fetches              1593478               0         1593478         1336007          257471               0"
    # The columns are: Label (variable), Total, Instrn, Data, Read, Write, Misc
    
    # We will look for specific labels
    labels_of_interest = [
        "Demand Fetches",
        "Demand Misses",
        "Demand miss rate"
    ]
    
    single_value_labels = {
        "Bytes From Memory": "bytes_from_memory", 
        "Bytes To Memory": "bytes_to_memory",
        "Total Bytes r/w Mem": "total_bytes_rw_mem"
    }

    current_line = ""
    current_cache_section = None
    
    # Cache section regex
    # Matches l1-icache, l1-dcache, l2-ucache, l1-I/Dcaches etc.
    cache_header_regex = re.compile(r"^l\d+-[a-zA-Z0-9/]+cache[s]?")

    try:
        lines = sys.stdin.readlines()
    except Exception as e:
        print(f"Error reading stdin: {e}", file=sys.stderr)
        return

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for cache section header
        if cache_header_regex.match(line):
            current_cache_section = line.split()[0]
            if current_cache_section not in data:
                data[current_cache_section] = {}
            continue

        # If we are inside a cache section
        if current_cache_section:
            target_dict = data[current_cache_section]
            
            # Parse matrix/table rows
            for label in labels_of_interest:
                if line.startswith(label):
                    # Extract all numbers (int or float)
                    # regex for float or int: -?\d+(\.\d+)?
                    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
                    
                    # Map to columns: Total, Instrn, Data, Read, Write, Misc
                    if len(nums) >= 6:
                        key = label.lower().replace(" ", "_")
                        target_dict[key] = {
                            "total": float(nums[0]),
                            "instrn": float(nums[1]),
                            "data": float(nums[2]),
                            "read": float(nums[3]),
                            "write": float(nums[4]),
                            "misc": float(nums[5])
                        }
            
            # Parse single values
            for label, key in single_value_labels.items():
                if line.startswith(label):
                    # We expect one number at the end usually
                    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
                    if nums:
                        target_dict[key] = float(nums[0])

    print(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()

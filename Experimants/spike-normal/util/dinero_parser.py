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
    
    try:
        lines = sys.stdin.readlines()
    except Exception as e:
        print(f"Error reading stdin: {e}", file=sys.stderr)
        return

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Parse matrix/table rows
        for label in labels_of_interest:
            if line.startswith(label):
                # The rest of the line are the values.
                # Remove the label from the line to parse the numbers
                # Be careful if label is "Demand Fetches", we want to ensure we don't match "Demand Fetches Something else" if that existed
                # specific check:
                
                # Check directly if the stripped line starts with the label
                # Extract the numbers.
                # "Demand Fetches" is 2 words. 
                # "Demand miss rate" is 3 words.
                
                # Let's just find all numbers in the line.
                # Assuming the label doesn't contain numbers.
                # Scientific notation is possible? Dinero usually prints standard floats or integers.
                
                # Extract all numbers (int or float)
                # regex for float or int: -?\d+(\.\d+)?
                nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
                
                # Map to columns: Total, Instrn, Data, Read, Write, Misc
                if len(nums) >= 6:
                    key = label.lower().replace(" ", "_")
                    data[key] = {
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
                # "Total Bytes r/w Mem         7006768"
                nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
                if nums:
                    # usually the last number is the value, or the first number after label?
                    # "Bytes From Memory           5901152" -> 5901152
                    # There is only one number usually.
                    data[key] = float(nums[0])

    print(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()

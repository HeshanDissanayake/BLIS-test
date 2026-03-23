import os
import json
import argparse
import sys
import re

# --- Scaling Configuration ---
# Define the scaling map here. Format: { calculated_value: scaling_factor }
SCALING_MAP = {
    # Example: 6144: 0.5,
}

def calculate_scaling_key(params):
    """
    Calculate the value used to look up the scaling factor.
    By default, calculates params['MC'] * params['KC'].
    """
    mr = params.get('MR', 0)
    nr = params.get('NR', 0)
    return mr * nr

def get_scaling_factor(params):
    key = calculate_scaling_key(params)
    # Default to 1.0 if key not in map
    return SCALING_MAP.get(key, 1.0)

def parse_directory_params(path):
    """Parses parameters from directory path segments like 'MC3072' -> {'MC': 3072}."""
    params = {}
    # Split path and iterate parts (filtering empty strings)
    for part in filter(None, path.split(os.sep)):
        # Match name (letters/numbers/underscores) followed by digits at end
        match = re.match(r"([A-Za-z0-9_]+?)(\d+)$", part)
        if match:
            k, v = match.groups()
            # Remove trailing underscore if present (e.g. L1_32 -> L1)
            if k.endswith('_'):
                k = k[:-1]
            params[k] = int(v)
    return params

# -----------------------------

def get_nested_value(data, key_path):
    keys = key_path.split('.')
    value = data
    try:
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
    except (KeyError, TypeError):
        return None

def main():
    parser = argparse.ArgumentParser(description="Process analyzed data by extracting a specific key.")
    parser.add_argument("dir_name", help="The experiment directory name (e.g., experiment-20-decoy)")
    parser.add_argument("--key", help="The key to extract from avg.json (supports dot notation, e.g., key.subkey). If omitted, the entire file is copied.", default=None)
    args = parser.parse_args()

    # Assuming script is run from the directory containing the experiment folder, or passed as full path
    base_dir = args.dir_name
    
    if not os.path.isdir(base_dir):
        # try joining with cwd
        base_dir = os.path.join(os.getcwd(), args.dir_name)
        if not os.path.isdir(base_dir):
            print(f"Error: Directory '{args.dir_name}' not found.")
            sys.exit(1)

    analysed_dir = os.path.join(base_dir, "analysed_data")
    processed_dir = os.path.join(base_dir, "processed_data")

    if not os.path.exists(analysed_dir):
        print(f"Error: '{analysed_dir}' does not exist.")
        sys.exit(1)

    print(f"Processing data from {analysed_dir}...")
    if args.key:
        print(f"Extracting key: '{args.key}' into {processed_dir}")
    else:
        print(f"Copying all data into {processed_dir}")
    
    count = 0
    for root, dirs, files in os.walk(analysed_dir):
        for file in files:
            if file == "avg.json":
                input_path = os.path.join(root, file)
                
                # Determine relative path structure
                rel_path = os.path.relpath(root, analysed_dir)
                output_dir_path = os.path.join(processed_dir, rel_path)
                output_path = os.path.join(output_dir_path, file)

                try:
                    with open(input_path, 'r') as f:
                        data = json.load(f)
                    
                    output_data = data
                    if args.key:
                        extracted_value = get_nested_value(data, args.key)
                        
                        if extracted_value is not None:
                            # Apply scaling if value is found and numeric
                            if isinstance(extracted_value, (int, float)):
                                params = parse_directory_params(rel_path)
                                # Calculate scaling key
                                key = calculate_scaling_key(params)
                                # Lookup scaling factor
                                scale_factor = SCALING_MAP.get(key, 1.0)
                                if scale_factor != 1.0:
                                    extracted_value = extracted_value * scale_factor
                                    # print(f"Scaled {input_path} by {scale_factor} (Key: {key})")

                            # Construct output object with the leaf key
                            leaf_key = args.key.split('.')[-1]
                            output_data = {leaf_key: extracted_value}
                        else:
                            # Key not found, skip writing
                            continue

                    os.makedirs(output_dir_path, exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(output_data, f, indent=4)
                    count += 1
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")

    print(f"Done. Processed {count} files. Output saved to {processed_dir}")

if __name__ == "__main__":
    main()

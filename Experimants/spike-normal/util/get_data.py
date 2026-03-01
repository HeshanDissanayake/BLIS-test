#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path

def recursive_sum(accumulator, new_data):
    """
    Recursively sums values from new_data into accumulator.
    """
    for key, value in new_data.items():
        if isinstance(value, dict):
            if key not in accumulator:
                accumulator[key] = {}
            recursive_sum(accumulator[key], value)
        elif isinstance(value, (int, float)):
            if key not in accumulator:
                accumulator[key] = 0.0
            accumulator[key] += value

def recursive_average(accumulator, count):
    """
    Recursively divides values in accumulator by count.
    """
    for key, value in accumulator.items():
        if isinstance(value, dict):
            recursive_average(value, count)
        elif isinstance(value, (int, float)):
            accumulator[key] = value / count

def main():
    if len(sys.argv) < 6:
        print("Usage: get_data.py L1_SIZE L1_LW L1_ASC <memtrace path> <memtrace root>")
        sys.exit(1)

    # Parse arguments
    l1_size_arg = sys.argv[1] # e.g., "32" (kb)
    l1_lw_arg = sys.argv[2]   # e.g., "16" (bytes)
    l1_asc_arg = sys.argv[3]  # e.g., "4" (ways)
    memtrace_path = sys.argv[4]
    memtrace_root_arg = sys.argv[5]

    # Resolve paths
    util_dir = Path(__file__).parent.resolve()
    run_dinero_cmd = util_dir / "run_dinero_json.sh"
    
    memtrace_root = Path(memtrace_root_arg)
    memtrace_complete = memtrace_root / memtrace_path
    
    if not memtrace_complete.exists() or not memtrace_complete.is_dir():
        print(f"Error: Trace directory directory '{memtrace_complete}' not found.")
        sys.exit(1)

    # Configure Environment for Dinero
    # Assuming input size is in kB for L1_SIZE, we probably need to append 'k' if not present
    # But usually config passes "32", Dinero wants "32k"
    l1_size_str = l1_size_arg if l1_size_arg.lower().endswith('k') else f"{l1_size_arg}k"
    
    env = os.environ.copy()
    
    # Mapping args to Dinero params. 
    # Applying L1_SIZE to D-cache (variable) and preserving I-cache default or setting both?
    # Previous tests varied specific params. Let's apply to D-cache heavily as that's often the focus for GEMM.
    # But often L1_SIZE implies uniform cache sizing in experiments.
    # I will set D-cache specific params based on args, and I-cache ?? 
    # Let's set both to be safe for a general "L1 Config" sweep.
    
    env["L1_ISIZE"] = l1_size_str
    env["L1_DSIZE"] = l1_size_str
    
    env["L1_IBSIZE"] = l1_lw_arg
    env["L1_DBSIZE"] = l1_lw_arg
    
    env["L1_IASSOC"] = l1_asc_arg
    env["L1_DASSOC"] = l1_asc_arg

    # Find files
    files = [f for f in memtrace_complete.iterdir() if f.is_file() and not f.name.startswith('.')]
    total_files = len(files)
    
    if total_files == 0:
        print(f"No files found in {memtrace_complete}")
        sys.exit(0)

    print(f"Processing {total_files} files in {memtrace_complete}...")
    print(f"Config: Size={l1_size_str}, BS={l1_lw_arg}, Assoc={l1_asc_arg}")

    accumulator = {}
    valid_files = 0

    for i, filepath in enumerate(files):
        # Progress
        print(f"[{i+1}/{total_files}] Running Dinero on {filepath.name}...", end='\r')
        
        try:
            # Run the bash script
            result = subprocess.run(
                [str(run_dinero_cmd), str(filepath)],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            recursive_sum(accumulator, data)
            valid_files += 1
            
        except subprocess.CalledProcessError as e:
            print(f"\n[!] Error running dinero on {filepath.name}: {e.stderr}")
        except json.JSONDecodeError:
             print(f"\n[!] Failed to parse JSON for {filepath.name}")
        except Exception as e:
            print(f"\n[!] Unexpected error: {e}")

    print(f"\nProcessing complete. {valid_files} valid outputs.")

    if valid_files > 0:
        # Calculate Average
        recursive_average(accumulator, valid_files)
        
        # Save Result
        # Output path: analysed_data/L1_{L1_SIZE}/LW{L1_LW}/ASC{L1_ASC}/{memtrace path}
        cwd = Path(os.getcwd())
        output_dir = cwd / "analysed_data" / f"L1_{l1_size_arg}" / f"LW{l1_lw_arg}" / f"ASC{l1_asc_arg}" / memtrace_path
        output_dir.mkdir(parents=True, exist_ok=True)
        
        avg_path = output_dir / "avg.json"
        with open(avg_path, "w") as f:
            json.dump(accumulator, f, indent=4)
            
        print(f"Averaged data saved to: {avg_path}")
    else:
        print("No valid data collected.")

if __name__ == "__main__":
    main()

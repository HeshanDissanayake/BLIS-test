import sys
import re
import os
import json

def parse_log(work_dir):
    log_path = os.path.join(work_dir, "screen_session_512.log")
    if not os.path.exists(log_path):
        print(f"Error: File {log_path} not found.")
        return

    # Regex for the command line
    # Expected format: ./MC_3072_KC_1024_NC_3072_gemm_blis_2x6 64 64 64
    # We look for the patterns MC_... inside the line
    cmd_pattern = re.compile(r'MC_(\d+)_KC_(\d+)_NC_(\d+)_gemm_blis_(\d+)x(\d+)\s+(\d+)\s+(\d+)\s+(\d+)')
    
    # Regex for data
    # Expected format: N,64,cycles,5215189,instret,1808850
    data_pattern = re.compile(r'N,(\d+),cycles,(\d+),instret,(\d+)')

    current_config = None
    
    # Determine output base directory (relative to where script is run, or relative to log?)
    # "placed in a dir as analysed_data/..."
    # I'll place it relative to the log file location so it stays with the experiment data.
    base_dir = os.path.dirname(os.path.abspath(log_path))
    analysed_dir = os.path.join(base_dir, "analysed_data")

    print(f"Parsing {log_path}...")
    
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Check for command line which sets the context for the next result
            # We look for "MC_" "KC_" etc within the line.
            if "MC_" in line and "KC_" in line and "gemm_blis" in line:
                 match = cmd_pattern.search(line)
                 if match:
                     mc, kc, nc, mr, nr, n1, n2, n3 = match.groups()
                     current_config = {
                         'MC': mc,
                         'KC': kc,
                         'NC': nc,
                         'MR': mr,
                         'NR': nr,
                         'args': [n1, n2, n3]
                     }
                     # print(f"Found config: {current_config}")
                     continue

            # Check for data line
            if current_config and line.startswith('N,'):
                match = data_pattern.search(line)
                if match:
                    n_val, cycles, instret = match.groups()
                    
                    # Construct directory path
                    output_dir = os.path.join(
                        analysed_dir,
                        f"MC_{current_config['MC']}",
                        f"KC_{current_config['KC']}",
                        f"NC_{current_config['NC']}",
                        f"MR_{current_config['MR']}",
                        f"NR_{current_config['NR']}"
                    )
                    
                    os.makedirs(output_dir, exist_ok=True)
                    
                    new_entry = {
                        "N": int(n_val),
                        "cycles": int(cycles),
                        "instret": int(instret)
                    }
                    
                    json_path = os.path.join(output_dir, "avg.json")
                    
                    with open(json_path, 'w') as jf:
                        json.dump(new_entry, jf, indent=2)
                        
                    print(f"Saved: {json_path} (N={n_val})")
                    
                    # Reset current config is optional depending on log structure 
                    # If multiple result lines follow one command, don't reset.
                    # But the example shows one result per command block.
                    # I'll keep current_config until overwritten by next command to be safe, 
                    # unless we want to strictly link one command line to one result line.
                    # Given the log flow ... command ... result ... done, it's safer to keep it 
                    # until a new command is seen, but what if a run fails?
                    # The current logic will just use the last seen config.
                    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 FPGA_log_analyser.py <directory>")
        sys.exit(1)
    
    parse_log(sys.argv[1])

#!/usr/bin/env python3
import os
import sys
import signal
import concurrent.futures
import multiprocessing

# Global flag to handle interrupts gracefully
stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    print("\n[!] Interrupt received. Signal set to stop...")
    stop_requested = True

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def is_valid_line(line):
    """
    Validates that a line has exactly 3 space-separated values.
    e.g. 'r 0x3fffc40ec8 8' is valid, 'w 0x3fffc4038' is not.
    Empty/whitespace-only lines are also considered invalid.
    """
    parts = line.strip().split()
    return len(parts) == 3

def has_split_text(filepath, split_text):
    """
    Checks if the file contains the split_text.
    """
    # For very large files, scanning fully is expensive. 
    # But checking strictly for existence requires reading.
    # We can try to optimize by reading in larger chunks, 
    # or just assume if we are calling this tool, we intend to split.
    # However, to be compliant with the logic "scan then split", we must check.
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Check the first few lines first for quick hit? 
            # Often LOG_MARKER is at start.
            header = f.read(4096)
            if split_text in header:
                return True
                
            # If not in header, read the rest in chunks
            while True:
                chunk = f.read(1024 * 1024) # 1MB chunks
                if not chunk:
                    break
                # Handle edge case where split_text is on chunk boundary? 
                # (Simple contains check might miss it if split across chunks, 
                # but "LOG_MARKER" is short enough and usually on a line).
                # To be safe, we could prepend last few chars of prev chunk, 
                # but for this specific "LOG_MARKER" use case, simple block check is usually sufficient 
                # or just reading line by line is safer but slower.
                if split_text in chunk:
                    return True
    except:
        pass
    return False

def split_file_task(args):
    """
    Worker function for parallel execution.
    args: (filepath, split_text)
    """
    filepath, split_text = args
    
    # We can't easily access global stop_requested across processes properly without Manager, 
    # but Pool handles termination. We'll add a basic check.
    
    dir_path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    
    # Optional: re-check locally if needed, but we do filtering before submit.
    
    try:
        part_num = 1
        name_part, ext_part = os.path.splitext(filename)
        
        current_out_path = os.path.join(dir_path, f"{name_part}_{part_num}{ext_part}")
        
        f_in = open(filepath, 'r', encoding='utf-8', errors='ignore')
        f_out = open(current_out_path, 'w', encoding='utf-8')
        
        removed_lines = 0
        total_lines = 0
        
        for line in f_in:
            if split_text in line:
                f_out.close()
                part_num += 1
                current_out_path = os.path.join(dir_path, f"{name_part}_{part_num}{ext_part}")
                f_out = open(current_out_path, 'w', encoding='utf-8')
            else:
                total_lines += 1
                if is_valid_line(line):
                    f_out.write(line)
                else:
                    removed_lines += 1
                
        f_in.close()
        f_out.close()

        if part_num > 1:
            # Split happened, remove original
            os.remove(filepath)
        else:
            # No split marker found, replace original with filtered version
            os.remove(filepath)
            os.rename(current_out_path, filepath)
        
        return (filename, part_num, removed_lines, total_lines)

    except Exception as e:
        return (filename, 0, 0, 0, str(e))

def scan_files(root_dir, split_text):
    print("[-] Scanning directory tree for files...")
    file_list = []
    count = 0
    
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            # Skip generated parts
            if "_" in filename and any(char.isdigit() for char in filename):
                continue
            
            filepath = os.path.join(root, filename)
            count += 1
            file_list.append((filepath, split_text))
            if count % 100 == 0:
                sys.stdout.write(f"\rFound {count} files...")
                sys.stdout.flush()
    
    print(f"\n[-] Total files to process: {len(file_list)}\n")
    return file_list

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 recursive_split_parallel.py <root_dir> <split_text> [num_threads]")
        sys.exit(1)

    root_dir = sys.argv[1]
    split_text = sys.argv[2]
    
    # Number of workers
    if len(sys.argv) > 3:
        max_workers = int(sys.argv[3])
    else:
        max_workers = multiprocessing.cpu_count()

    file_list = scan_files(root_dir, split_text)
    
    if not file_list:
        print("No files found.")
        sys.exit(0)

    print(f"[-] Starting parallel processing with {max_workers} workers.")
    print("Press Ctrl+C to stop (may take a moment to terminate all workers).")

    completed = 0
    total = len(file_list)
    summary = []

    try:
        # Use ProcessPoolExecutor for CPU-bound file processing (read/write/string search)
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(split_file_task, args): args[0] for args in file_list}
            
            for future in concurrent.futures.as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    result = future.result()
                    completed += 1
                    percentage = (completed / total) * 100
                    
                    if isinstance(result, tuple):
                        if len(result) == 5:
                            # Error case
                            fname, _, _, _, err = result
                            summary.append((fname, 0, 0, 0, err))
                            print(f"  [{completed}/{total}] ({percentage:5.1f}%) ERROR  {filepath}: {err}")
                        else:
                            fname, parts, removed, total_lines = result
                            summary.append((fname, parts, removed, total_lines, None))
                            split_info = f"{parts} parts" if parts > 1 else "no split"
                            print(f"  [{completed}/{total}] ({percentage:5.1f}%) {filepath}  [{split_info}, {removed} removed / {total_lines} lines]")
                except Exception as exc:
                    print(f"  [!] Generated exception for {filepath}: {exc}")

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Shutting down pool...")
        sys.exit(1)
    
    # Print summary
    print("\n\n" + "="*70)
    print("FILTERING SUMMARY")
    print("="*70)
    total_removed = 0
    total_all_lines = 0
    for entry in summary:
        fname, parts, removed, total_lines, err = entry
        if err:
            print(f"  {fname} -- ERROR: {err}")
        else:
            total_removed += removed
            total_all_lines += total_lines
            print(f"  {fname} -- {removed} illegal lines removed (out of {total_lines})")
    print("-"*70)
    print(f"  TOTAL: {total_removed} illegal lines removed (out of {total_all_lines})")
    print("="*70)
    print("\n[-] All processing complete.")

if __name__ == "__main__":
    main()

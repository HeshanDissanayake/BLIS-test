#!/usr/bin/env python3
import os
import sys
import signal

# Global flag to handle interrupts gracefully
stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    print("\n[!] Interrupt received. Stopping after current operation...")
    stop_requested = True

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

def has_split_text(filepath, split_text):
    """
    Checks if the file contains the split_text.
    """
    try:
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                if split_text in line:
                    return True
    except:
        pass
    return False

def split_file(filepath, split_text):
    """
    Splits the file at lines containing split_text.
    Removes the split_text line.
    Deletes the original file ONLY if successful and not interrupted.
    """
    global stop_requested
    
    dir_path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    base_name = os.path.splitext(filename)[0]
    
    # Check if we should even process this file
    if not has_split_text(filepath, split_text):
        return False
        
    print(f"[*] Processing: {filepath}")
    
    try:
        part_num = 1
        name_part, ext_part = os.path.splitext(filename)
        # Use original extension, don't force .txt
            
        current_out_path = os.path.join(dir_path, f"{name_part}_{part_num}{ext_part}")
        
        f_in = open(filepath, 'r')
        f_out = open(current_out_path, 'w')
        
        found_split = False
        
        for line in f_in:
            if stop_requested:
                f_in.close()
                f_out.close()
                print(f"[-] Aborted processing of {filepath} due to interrupt.")
                return False
                
            if split_text in line:
                # Split detected. Close current, start next.
                # Do NOT write the split line.
                f_out.close()
                part_num += 1
                current_out_path = os.path.join(dir_path, f"{name_part}_{part_num}{ext_part}")
                f_out = open(current_out_path, 'w')
                found_split = True
            else:
                f_out.write(line)
                
        f_in.close()
        f_out.close()
        
        if stop_requested:
             print(f"[-] Finised {filepath} but interrupt pending. NOT deleting original.")
             return False

        # Verify we actually did something? 
        # The file contained the split text (checked at start), so we definitely split or at least consumed it.
        # If we just copied the file because text was at the very end...
        
        print(f"  -> Split into {part_num} files.")
        
        # Deletion logic removed by request.
        # os.remove(filepath)
        # print(f"  -> Deleted original: {filename}")
        return True

    except Exception as e:
        print(f"[!] Error processing {filepath}: {e}")
        return False

def count_work(root_dir, split_text):
    """
    Counts total files to process for progress bar.
    """
    print("[-] Scanning directory tree to count files...")
    count = 0
    file_list = []
    try:
        for root, dirs, files in os.walk(root_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                # Avoid re-splitting files we likely generated
                if "_" in filename and any(char.isdigit() for char in filename):
                     continue
                     
                if has_split_text(filepath, split_text):
                    count += 1
                    file_list.append(filepath)
                    # Simple progress indicator for scanning
                    if count % 100 == 0:
                        sys.stdout.write(f"\rFound {count} files...")
                        sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted.")
        return [], 0
        
    print(f"\n[-] Total files to process: {count}\n")
    return file_list, count

def main():
    global stop_requested
    
    if len(sys.argv) < 3:
        print("Usage: python3 recursive_split.py <root_dir> <split_text>")
        print("Example: python3 recursive_split.py ./experiments 'GEMM_END'")
        sys.exit(1)

    root_dir = sys.argv[1]
    split_text = sys.argv[2]
    
    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a directory.")
        sys.exit(1)

    print(f"Starting recursive split in {root_dir}")
    print(f"Split text: '{split_text}'")
    print("Press Ctrl+C to stop safely (current file will complete).")

    # Phase 1: Count
    files_to_process, total_files = count_work(root_dir, split_text)
    
    if total_files == 0:
        print("No files found matching the criteria.")
        sys.exit(0)

    # Phase 2: Process
    processed_count = 0
    
    for filepath in files_to_process:
        if stop_requested:
            break
            
        processed_count += 1
        percentage = (processed_count / total_files) * 100
        print(f"[{processed_count}/{total_files}] ({percentage:.1f}%) Processing: {os.path.basename(filepath)}")
        
        split_file(filepath, split_text)
            
    if stop_requested:
        print("\nProcess stopped by user.")
        sys.exit(1) 
    else:
        print("\nAll processing complete.")

if __name__ == "__main__":
    main()

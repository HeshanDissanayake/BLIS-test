#!/usr/bin/env bash

# Check arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <input_file> <split_text> <output_prefix>"
    echo "Example: $0 huge_log.txt 'PROCESS_END' ./split/part"
    exit 1
fi

INPUT_FILE="$1"
SPLIT_TEXT="$2"
OUTPUT_PREFIX="$3"

# Create output directory if the prefix contains a directory path
OUTPUT_DIR=$(dirname "$OUTPUT_PREFIX")
mkdir -p "$OUTPUT_DIR"

# Use awk for efficient processing
awk -v pattern="$SPLIT_TEXT" -v prefix="$OUTPUT_PREFIX" '
BEGIN { 
    count=1; 
    file=prefix "_" count ".txt" 
}
{
    # If the line contains the split text (literal match), move to next file
    if (index($0, pattern) > 0) {
        close(file)
        count++
        file=prefix "_" count ".txt"
    } else {
        # Print the current line to the current file
        print > file
    }
}
' "$INPUT_FILE"

echo "Splitting complete. Files created with prefix: ${OUTPUT_PREFIX}_"

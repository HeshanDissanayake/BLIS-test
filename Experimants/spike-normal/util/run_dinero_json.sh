#!/usr/bin/env bash

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <dinero_input_file>"
    exit 1
fi

INPUT_FILE="$1"
UTIL_DIR=$(dirname "$0")

# Configuration with defaults (support env var overrides)
# Ensure units (k) are handled by caller or defaults
L1_ISIZE=${L1_ISIZE:-8k}
L1_DSIZE=${L1_DSIZE:-640k}
L1_IBSIZE=${L1_IBSIZE:-16}
L1_DBSIZE=${L1_DBSIZE:-16}
L1_IASSOC=${L1_IASSOC:-2}
L1_DASSOC=${L1_DASSOC:-1}

# Dinero flags
FLAGS="-l1-isize $L1_ISIZE \
    -l1-ibsize $L1_IBSIZE \
    -l1-iassoc $L1_IASSOC \
    -l1-irepl l \
    -l1-ifetch d \
    -l1-dsize $L1_DSIZE \
    -l1-dbsize $L1_DBSIZE \
    -l1-dassoc $L1_DASSOC \
    -l1-drepl f \
    -l1-dfetch d \
    -l1-dwalloc a \
    -l1-dwback a \
    -flushcount 10k \
    -stat-idcombine \
    -informat D"

# Run dinero and pipe to parser
dineroIV $FLAGS < "$INPUT_FILE" | python3 "${UTIL_DIR}/dinero_parser.py"

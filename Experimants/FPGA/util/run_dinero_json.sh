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
L1_ISIZE=${L1_ISIZE:-32k}
L1_DSIZE=${L1_DSIZE:-32k}
L1_IBSIZE=${L1_IBSIZE:-16}
L1_DBSIZE=${L1_DBSIZE:-16}
L1_IASSOC=${L1_IASSOC:-8}
L1_DASSOC=${L1_DASSOC:-8}

# L2 defaults
L2_USIZE=${L2_USIZE:-128k}
L2_UBSIZE=${L2_UBSIZE:-64}
L2_UASSOC=${L2_UASSOC:-8}

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
    -l2-usize $L2_USIZE \
    -l2-ubsize $L2_UBSIZE \
    -l2-uassoc $L2_UASSOC \
    -l2-urepl f \
    -l2-ufetch d \
    -l2-uwalloc a \
    -l2-uwback a \
    -flushcount 10k \
    -stat-idcombine \
    -informat D"

# Run dinero and pipe to parser
dineroIV $FLAGS < "$INPUT_FILE" | python3 "${UTIL_DIR}/dinero_parser.py"

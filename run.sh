#!/bin/sh

BENCH=./gemm_riscv_generic

# Check if the executable exists
if [ ! -x "$BENCH" ]; then
    echo "Error: $BENCH not found or not executable"
    exit 1
fi

# Loop from 16 to 1024 in steps of 16
N=16
while [ $N -le 1024 ]; do
    "$BENCH" $N
    N=$((N + 16))
done

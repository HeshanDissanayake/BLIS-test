#!/usr/bin/env bash
exp_dir=$1

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1

/home/heshds/working_dir/riscv-isa-sim-dev/build/spike bbl



#!/usr/bin/env bash
exp_dir=$1
RISCV_SDK=/home/heshds/working_dir/cva6-sdk/

export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v ' ' | paste -sd: -) 

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1

# build all the requried blis executables and copy to sdk and build linux and copy to a dir
cat config.json \
| python3 ../../Experiment_tools/expand_config.py -i MC,NC,KC\
| python3 ../../Experiment_tools/run_per_config.py ../util/build_linux_per_config.sh MC NC KC || exit 1




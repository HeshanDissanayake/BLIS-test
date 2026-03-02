#!/usr/bin/env bash
exp_dir=$1

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1


SPIKE_DIR=spike
EXP_TOOLS=/home/heshds/working_dir/BLIS-test/Experimants/Experiment_tools
IMG_DIR=/home/heshds/working_dir/BLIS-test/Experimants/spike-normal/images
UTIL=/home/heshds/working_dir/BLIS-test/Experimants/spike-normal/util

# SPIKE_DIR=/home/heshds/working_dir/cva6-sdk/riscv-isa-sim/build/spike
# EXP_TOOLS=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/Experiment_tools
# IMG_DIR=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/images
# UTIL=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/util


cat config.json \
| python3 ${EXP_TOOLS}/expand_config.py -i MC,NC,KC,MR,N_start,N_end,N_step \
| python3 ${EXP_TOOLS}/run_per_config.py  ${UTIL}/spike.expect  MC NC KC MR N_start N_end N_step -a "${SPIKE_DIR}" -a "${IMG_DIR}" 

     





     

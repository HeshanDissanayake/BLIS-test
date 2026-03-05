#!/usr/bin/env bash
exp_dir=$1

ROOT=$(pwd)
SPIKE_DIR=/home/heshds/working_dir/cva6-sdk/riscv-isa-sim/build/spike
EXP_TOOLS=${ROOT}/../Experiment_tools
IMG_DIR=${ROOT}/images
UTIL=${ROOT}/util

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1

cat config.json \
| python3 ${EXP_TOOLS}/expand_config.py -i L1_SIZE,L1_LW,L1_ASC,MC,NC,KC,MR,NR,N_start,N_end,N_step \
| python3 ${EXP_TOOLS}/run_per_config.py  ${UTIL}/spike.expect  MC NC KC MR NR N_start N_end N_step -a "${SPIKE_DIR}" -a "${IMG_DIR}" 

     
# python3 ${ROOT}/util/recursive_split_parallel.py ${ROOT}/${exp_dir}/memtraces "LOG MARKER"




     

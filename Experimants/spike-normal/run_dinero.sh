#!/usr/bin/env bash
exp_dir=$1
EXP_TOOLS=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/Experiment_tools
UTIL=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/util
MEMTRACE_PATH=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-1/


# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1

# Run cache analyser(dinero) per memtrace(MC,NC,KC,MR)
cat config.json \
| python3 ${EXP_TOOLS}/expand_config.py -i MC,NC,KC,MR\
| python3 ${EXP_TOOLS}/run_per_config.py ${UTIL}/run_per_memtrace.sh MC NC KC MR 

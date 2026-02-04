#!/usr/bin/env bash
exp_dir=$1

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi

cd "${exp_dir}" || exit 1

# run simulations for all cache configurations
cat config.json \
| python3 ../../Experiment_tools/expand_config.py -i  L1_SIZE,L1_LW,L1_ASC \
| python3 ../../Experiment_tools/run_per_config.py ../util/run-spike.sh L1_SIZE L1_LW L1_ASC

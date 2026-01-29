#!/usr/bin/env bash
set -e

SPIKE_DIR=/home/heshds/working_dir/spike-flexicas/spike-flexicas
SPIKE_BUILD_DIR=/home/heshds/working_dir/BLIS-test/Experimants/flexicas/prebuilt_spikes
EXP_TOOLS=/home/heshds/working_dir/BLIS-test/Experimants/Experiment_tools
UTIL=/home/heshds/working_dir/BLIS-test/Experimants/flexicas/util


L1_SIZE=$1
L1_LW=$2
L1_ASC=$3

spike_config="L1_${L1_SIZE}_LW${L1_LW}_ASC${L1_ASC}"
spike="${SPIKE_BUILD_DIR}/${spike_config}/spike"

main_dir=$(pwd)
exp_dir="L1_${L1_SIZE}/LW${L1_LW}/ASC${L1_ASC}"

mkdir -p ${exp_dir}
cd "${exp_dir}" || exit 1

# build all the requried blis executables
cat ${main_dir}/config.json \
| python3 ${EXP_TOOLS}/expand_config.py -i MC,NC,KC,MR,N_start,N_end,N_step \
| python3 ${EXP_TOOLS}/run_per_config.py  ${UTIL}/spike.expect  MC NC KC MR N_start N_end N_step -a "${spike}" -a "${main_dir}/bbl" 



# /home/heshds/working_dir/BLIS-test/Experimants/flexicas/util/spike.expect "${spike}" "${main_dir}/bbl"


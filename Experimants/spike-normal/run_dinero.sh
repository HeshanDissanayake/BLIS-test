ROOT=$(pwd)
cd ${1}

python3 ${ROOT}/../Experiment_tools/run_tasks.py \
  --config config.json \
  --params L1_SIZE L1_LW L1_ASC MC NC KC MR NR\
  --script ../util/run_per_memtrace.sh \
  --script_args "--EXP_DIR ${ROOT}/${1}" \
  -p
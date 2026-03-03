ROOT=$(pwd)
cd ${1}

python3 ${ROOT}/../Experiment_tools/run_tasks.py \
  --config config.json \
  --params MC NC KC MR \
  --script ../util/cycle_count_2_json.py \
  --script_args "--EXP_DIR ${ROOT}/${1}" \
  -p

  
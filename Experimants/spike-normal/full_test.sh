./build_linux.sh experiment-5
./run_memtrace.sh experiment-5

# python3 ./util/recursive_split_parallel.py /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/memtraces/MC4096 "LOG MARKER"

cd experiment-5
python3 ../../Experiment_tools/run_tasks.py \
  --config config.json \
  --params MC NC KC MR \
  --script ../util/run_per_memtrace.sh \
  --script_args "--EXP_DIR /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-5" \
  -p


# python3 analyse_json.py --root /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-4/analysed_data \
#                         --x KC --y demand_misses.total --x_subplot  MR --y_subplot ASC \
#                         --output_dir /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-4/plots --global_scale
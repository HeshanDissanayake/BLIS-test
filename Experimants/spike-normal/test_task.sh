#!/usr/bin/env bash


python3 ../../Experiment_tools/run_tasks.py \
  --config config.json \
  --params MC NC KC MR \
  --script ../util/run_per_memtrace.sh \
  --script_args "--MEMTRACE_PATH /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/memtraces" \
  -p



python3 util/analyse_json.py --root /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/analysed_data \
                                --x KC \
                                --y demand_misses.data \
                                --x_subplot MR \
                                --y_subplot L1 \
                                --neglect_dims MC NC \
                                --output_dir /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/plots/misses \
                                --global_scale 

python3 util/analyse_json.py --root /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/analysed_data \
                                --x KC \
                                --y demand_misses.read \
                                --x_subplot MR \
                                --y_subplot L1 \
                                --neglect_dims MC NC \
                                --output_dir /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-2/plots/misses_read \
                                --global_scale 



  - bytes_from_memory
  - bytes_to_memory
  - demand_fetches.data
  - demand_fetches.instrn
  - demand_fetches.misc
  - demand_fetches.read
  - demand_fetches.total
  - demand_fetches.write
  - demand_miss_rate.data
  - demand_miss_rate.instrn
  - demand_miss_rate.misc
  - demand_miss_rate.read
  - demand_miss_rate.total
  - demand_miss_rate.write
  - demand_misses.data
  - demand_misses.instrn
  - demand_misses.misc
  - demand_misses.read
  - demand_misses.total
  - demand_misses.write
  - total_bytes_rw_mem
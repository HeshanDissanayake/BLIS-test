# build BLIS and images form them
./build_linux.sh experiment-5

# run spike and collect memtraces and split them into separate files
./run_memtrace.sh experiment-5





# python3 analyse_json.py --root /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-4/analysed_data \
#                         --x KC --y demand_misses.total --x_subplot  MR --y_subplot ASC \
#                         --output_dir /home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/experiment-4/plots --global_scale
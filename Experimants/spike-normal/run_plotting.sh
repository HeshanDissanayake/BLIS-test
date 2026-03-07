ROOT=$(pwd)
exp=$1
shift

if [[ "$1" == "-list" ]]; then
    python3 util/analyse_json.py \
                        --root "$ROOT/$exp/analysed_data" \
                        --list_params
else
    python3 util/analyse_json.py \
                        --root "$ROOT/$exp/analysed_data" \
                        --x KC \
                        --y l1-i_dcaches.demand_misses.write \
                        --y_label "write misses" \
                        --neglect_dims L1_SIZE L1_LW L1_ASC MR NR\
                        --output_dir "$ROOT/$exp/plots" \
                        --global_scale  \
                        --x_ticks_from_data \
                        --secondary_x_formula "(KC * MR)/512" \
                        --secondary_x_label "CAr"

    # python3 util/analyse_json.py \
    #                     --root "$ROOT/$exp/cycles" \
    #                     --x KC \
    #                     --y 1024 \
    #                     --y_label "Instructions" \
    #                     --x_subplot  MR \
    #                     --y_subplot NC \
    #                     --output_dir "$ROOT/$exp/plots" \
    #                     --global_scale  \
    #                     --x_ticks_from_data \
    #                     --secondary_x_formula "(KC * MR)/512" \
    #                     --secondary_x_label "CAr"

    # python3 util/heatmap_json.py \
    # --root experiment-17/analysed_data \
    # --x MR --y NR \
    # --value \
    # l1-i_dcaches.total_bytes_rw_mem \
    # --annotate --global_scale \
    # --output_dir experiment-17/plots \
    # --x_ticks_from_data 

    # python3 util/heatmap_json.py \
    # --root experiment-17/cycles \
    # --x MR --y NR \
    # --value \
    # 512 \
    # --annotate --global_scale \
    # --output_dir experiment-17/plots \
    # --x_ticks_from_data 

fi

# analysed_data

#   - l1-i_dcaches.bytes_from_memory
#   - l1-i_dcaches.bytes_to_memory
#   - l1-i_dcaches.demand_fetches.data
#   - l1-i_dcaches.demand_fetches.instrn
#   - l1-i_dcaches.demand_fetches.misc
#   - l1-i_dcaches.demand_fetches.read
#   - l1-i_dcaches.demand_fetches.total
#   - l1-i_dcaches.demand_fetches.write

#   - l1-i_dcaches.demand_miss_rate.data
#   - l1-i_dcaches.demand_miss_rate.instrn
#   - l1-i_dcaches.demand_miss_rate.misc
#   - l1-i_dcaches.demand_miss_rate.read
#   - l1-i_dcaches.demand_miss_rate.total
#   - l1-i_dcaches.demand_miss_rate.write

#   - l1-i_dcaches.demand_misses.data
#   - l1-i_dcaches.demand_misses.instrn
#   - l1-i_dcaches.demand_misses.misc
#   - l1-i_dcaches.demand_misses.read
#   - l1-i_dcaches.demand_misses.total
#   - l1-i_dcaches.demand_misses.write
#   - l1-i_dcaches.total_bytes_rw_mem

#   - l2-ucache.bytes_from_memory
#   - l2-ucache.bytes_to_memory
#   - l2-ucache.demand_fetches.data
#   - l2-ucache.demand_fetches.instrn
#   - l2-ucache.demand_fetches.misc
#   - l2-ucache.demand_fetches.read
#   - l2-ucache.demand_fetches.total
#   - l2-ucache.demand_fetches.write
#   - l2-ucache.demand_miss_rate.data
#   - l2-ucache.demand_miss_rate.instrn
#   - l2-ucache.demand_miss_rate.misc
#   - l2-ucache.demand_miss_rate.read
#   - l2-ucache.demand_miss_rate.total
#   - l2-ucache.demand_miss_rate.write
#   - l2-ucache.demand_misses.data
#   - l2-ucache.demand_misses.instrn
#   - l2-ucache.demand_misses.misc
#   - l2-ucache.demand_misses.read
#   - l2-ucache.demand_misses.total
#   - l2-ucache.demand_misses.write
#   - l2-ucache.total_bytes_rw_mem


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
                        --y l1-i_dcaches.demand_misses.total \
                        --x_subplot  MR \
                        --y_subplot ASC \
                        --output_dir "$ROOT/$exp/plots" \
                        --global_scale
fi
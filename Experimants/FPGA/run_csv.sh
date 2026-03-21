#!/bin/bash
EXP=${1:-experiment-11}

python3 util/analyse_json.py \
  --root ${EXP}/cycles \
  --x KC \
  --y MR \
  --value 1024 \
  --neglect_dims L1_SIZE L1_LW L1_ASC \
  --label insts \
  --dump_csv ${EXP}/insts.csv


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
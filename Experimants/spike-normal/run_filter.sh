ROOT=$(pwd)
exp=$1
shift

  ./util/filter_heatmap.py \
  --root "$ROOT/$exp" \
  --x MR --y NR \
  --group "MR*NR" "min(l1-i_dcaches.demand_misses.total)" \


# --cascade "(MR + NR +(MR*NR))//32 == 0" "min(l1-i_dcaches.demand_misses.total)" \
#   --cascade "(MR + NR +(MR*NR))//32 == 1" "min(l1-i_dcaches.demand_misses.total)" \
#   --cascade "(MR + NR +(MR*NR))//32 == 2" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 3" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 4" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 5" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 6" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 7" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 8" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 9" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 10" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 11" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 12" "min(l1-i_dcaches.demand_misses.total)" \
#  --cascade "(MR + NR +(MR*NR))//32 == 13" "min(l1-i_dcaches.demand_misses.total)" \
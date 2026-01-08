#!/usr/bin/env bash
set -euo pipefail

source ../config/blis/all-2
source ../config/parser.sh

BLOCK_SIZES=($(parse_list "$MR"))

MR=($(parse_list "$MR"))
NR=($(parse_list "$NR"))
N=($(parse_list "$N"))
MC=($(parse_list "$MC"))
NC=($(parse_list "$NC"))
KC=($(parse_list "$KC"))


OUT=run_static.sh

# ----------------------------
# Generate static script
# ----------------------------
cat > "$OUT" <<EOF
#!/bin/sh
# this program is meant to be run on the FPGA with the linux distro
# wget http://10.65.196.56:8000/FPGA/run_static.sh -O run.sh

HOST_IP=10.65.196.56

EOF

echo "for mr in ${MR[*]}; do" >> "$OUT"
echo "  for nr in ${NR[*]}; do" >> "$OUT"
echo "    for mc in ${MC[*]}; do" >> "$OUT"
echo "      for nc in ${NC[*]}; do" >> "$OUT"
echo "        for kc in ${KC[*]}; do" >> "$OUT"
echo "          CACHE_PROFILE=MC_\${mc}_KC_\${kc}_NC_\${nc}" >> "$OUT"
echo "          #fetch files from the host" >> "$OUT"
echo "          wget http://\${HOST_IP}:8000/BLIS_exec/build/\${CACHE_PROFILE}/gemm_blis_\${mr}x\${nr} -O gemm_blis_\${mr}x\${nr}" >> "$OUT"
echo "          chmod u+x gemm_blis_\${mr}x\${nr}" >> "$OUT"
echo "          " >> "$OUT"    
echo "          for n in ${N[*]}; do" >> "$OUT"

cat >> "$OUT" <<'EOF'
                    echo "benchmark: gemm_blis_${mr}x${nr} ${CACHE_PROFILE}" 
                    exec="./gemm_blis_${mr}x${nr} ${n} ${n} ${n}"
                   ./$exec
EOF

echo "          done" >> "$OUT"
echo "        done" >> "$OUT"
echo "      done" >> "$OUT"
echo "    done" >> "$OUT"
echo "  done" >> "$OUT"
echo "done" >> "$OUT"

chmod +x "$OUT"

echo "Generated $OUT"

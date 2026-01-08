#!/usr/bin/env bash
set -euo pipefail

source ../../config/blis/all-1
source ../../config/parser.sh

BLOCK_SIZES=($(parse_list "$MR"))

MR=($(parse_list "$MR"))
NR=($(parse_list "$NR"))
N=($(parse_list "$N"))
# MC=($(parse_list "$MC"))
# NC=($(parse_list "$NC"))
# KC=($(parse_list "$KC"))

CONFIG=$1
OUT=run_static.sh

# ----------------------------
# Generate static script
# ----------------------------
cat > "$OUT" <<EOF
#!/bin/sh
# this program is meant to be run on the spike with the linux distro
EOF

echo "for mr in ${MR[*]}; do" >> "$OUT"
echo "echo benchmark: ./gemm_blis_\${mr}x\${mr} ${CONFIG}" >> "$OUT"
echo "  for n in ${N[*]}; do" >> "$OUT"

cat >> "$OUT" <<'EOF'
      exec="./gemm_blis_${mr}x${mr} ${n} ${n} ${n}"
      ./$exec
EOF

echo "  done" >> "$OUT"
echo "done" >> "$OUT"

chmod +x "$OUT"

echo "Generated $OUT"

#!/bin/sh
# this program is meant to be run on the FPGA
# wget http://10.65.196.56:8000/run.sh -O run.sh

HOST_IP=10.65.196.56

run_bench() {
    BENCH=$1

    echo " "
    echo "benchmark: $BENCH"

    N=16
    while [ $N -le 256 ]; do
        "$BENCH" $N $N $N
        N=$((N + 16))
    done

    "$BENCH" 512 512 512
}


MC_VALUES="16 32 64 96 128 256"

for MC in $MC_VALUES; do
  NC=$MC
  KC=64
  while [ $KC -le 640 ]; do

    CACHE_PROFILE=MC_${MC}_KC_${KC}_NC_${NC}

    # fetch files from the host
    wget http://${HOST_IP}:8000/build/${CACHE_PROFILE}/gemm_blis_4x4 -O gemm_blis_4x4
    wget http://${HOST_IP}:8000/build/${CACHE_PROFILE}/gemm_blis_8x8 -O gemm_blis_8x8
    wget http://${HOST_IP}:8000/build/${CACHE_PROFILE}/gemm_blis_16x16 -O gemm_blis_16x16

    chmod u+x gemm_blis_4x4  gemm_blis_8x8 gemm_blis_16x16 

    run_bench ./gemm_blis_4x4 ${CACHE_PROFILE}
    run_bench ./gemm_blis_8x8 ${CACHE_PROFILE}
    run_bench ./gemm_blis_16x16 ${CACHE_PROFILE}

    KC=$((KC + 64))
  done
done




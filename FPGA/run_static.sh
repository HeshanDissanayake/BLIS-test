#!/bin/sh
# this program is meant to be run on the FPGA with the linux distro
for mr in 4 8 16; do
  for nr in 4 8 16; do
    for mc in 4096; do
      for nc in 16; do
        for kc in 96 192 384; do
          CACHE_PROFILE=MC_${mc}_KC_${kc}_NC_${nc}
          #fetch files from the host
          wget http://${HOST_IP}:8000/build/${CACHE_PROFILE}/gemm_blis_${mr}x${nr} -O gemm_blis_${mr}x${nr}
          chmod u+x gemm_blis_${mr}x${nr}
          
          for n in 16 32 48 64 80 96 112 128 144 160 176 192 208 224 240 256 384 512 640 768 896 1024; do
                    echo "benchmark: gemm_blis_${mr}x${nr} ${CACHE_PROFILE}" 
                    exec="./gemm_blis_${mr}x${nr} ${n} ${n} ${n}"
                   ./$exec
          done
        done
      done
    done
  done
done

#!/bin/sh
# this program is meant to be run on the spike with the linux distro
for mr in 4 8 16; do
echo benchmark: ./gemm_blis_${mr}x${mr} spec
  for n in 16 32 48 64 80 96 112 128 144 160 176 192 208 224 240 256 512; do
      exec="./gemm_blis_${mr}x${mr} ${n} ${n} ${n}"
      ./$exec
  done
done

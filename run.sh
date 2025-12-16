#!/bin/sh
# this program is meant to be run on the FPGA
# wget http://10.65.196.56:8000/run.sh -O run.sh

HOST_IP=10.65.196.56
# fetch files from the host
wget http://${HOST_IP}:8000/gemm_blis_4x4 -O gemm_blis_4x4
wget http://${HOST_IP}:8000/gemm_blis_8x8 -O gemm_blis_8x8
wget http://${HOST_IP}:8000/gemm_blis_16x16 -O gemm_blis_16x16

wget http://${HOST_IP}:8000/gemm_blis_4x4 -O print_params_4x4 
wget http://${HOST_IP}:8000/gemm_blis_8x8 -O print_params_8x8
wget http://${HOST_IP}:8000/gemm_blis_16x16 -O print_params_16 x16

chmod u+x gemm_blis_4x4  
chmod u+x gemm_blis_8x8 
chmod u+x gemm_blis_16x16 

chmod u+x print_params_4x4 
chmod u+x print_params_8x8
chmod u+x print_params_16x16

BENCH=./gemm_blis_4x4
N=16
echo " "
./print_params_4x4
while [ $N -le 560 ]; do
    "$BENCH" $N $N $N
    N=$((N + 16))
done


BENCH=./gemm_blis_8x8
N=16
echo " "
./print_params_8x8
while [ $N -le 560 ]; do
    "$BENCH" $N $N $N
    N=$((N + 16))
done


BENCH=./gemm_blis_4x4
N=16
echo " "
./print_params_16x16
while [ $N -le 560 ]; do
    "$BENCH" $N $N $N
    N=$((N + 16))
done
#!/bin/bash
set -e

BLIS_LIB_DIR=/home/heshds/working_dir/BLIS/blis

MC=$1
NC=$2
KC=$3
MR=$4
NR=$5

pushd ${BLIS_LIB_DIR} > /dev/null

echo "========================================"
echo "Running build: MC=${MC}, NC=${NC}, KC=${KC}, MR=${MR}, NR=${NR}"
echo "========================================"

./build.sh -m ${MC} -n ${NC} -k ${KC} -mr ${MR} -nr ${NR}

popd > /dev/null

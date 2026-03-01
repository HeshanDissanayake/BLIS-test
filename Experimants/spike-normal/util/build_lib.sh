#!/bin/bash
set -e

BLIS_LIB_DIR=/home/heshds/working_dir/BLIS/blis

MC=$1
NC=$2
KC=$3

pushd ${BLIS_LIB_DIR} > /dev/null

echo "========================================"
echo "Running build: MC=${MC}, NC=${NC}, KC=${KC}"
echo "========================================"

./build.sh -m ${MC} -n ${NC} -k ${KC}

popd > /dev/null

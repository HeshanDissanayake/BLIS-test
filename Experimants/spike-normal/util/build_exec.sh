#!/usr/bin/env bash
set -e
BLIS_LIB_DIR=/opt/dev/blis
RISCV_SDK=/home/heshds/working_dir/cva6-sdk
IMG_DIR=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/images


MC=$1
NC=$2
KC=$3
MR=$4
NR=$5

REG_SIZE="${MR}x${NR}"

# check for library
CACHE_PROFILE="MC_${MC}_KC_${KC}_NC_${NC}"
if [ ! -d "${BLIS_LIB_DIR}/${CACHE_PROFILE}/blis_${REG_SIZE}" ]; then
    echo "BLIS library ${CACHE_PROFILE}/blis_${REG_SIZE} not found. Building..."
    ../util/build_lib.sh ${MC} ${NC} ${KC} ${MR} ${NR}
else
    echo "Using cached BLIS library ${CACHE_PROFILE}/blis_${REG_SIZE}"
fi

# Build the executable for the specific register size
make -C ../../../BLIS_exec CACHE_PROFILE=${CACHE_PROFILE} REG_SIZE=${REG_SIZE}


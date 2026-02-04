#!/usr/bin/env bash
set -e
BLIS_LIB_DIR=/opt/dev/blis
RISCV_SDK=/home/heshds/working_dir/spike-flexicas/riscv-spike-sdk/

MC=$1
NC=$2
KC=$3

MR=$4
NR=$5

# check for library
CACHE_PROFILE="MC_${MC}_KC_${KC}_NC_${NC}"
if [ ! -d "${BLIS_LIB_DIR}/${CACHE_PROFILE}" ]; then
    echo "BLIS library ${CACHE_PROFILE} not found. Building..."
    exit 1
else
    echo "Using cached BLIS library ${BLIS_DIR}"
    # TODO: build the lib
fi

# Build the executable
make -C ../../../BLIS_exec CACHE_PROFILE=${CACHE_PROFILE}

# copy it to the bbl rootfs
cp -r ../../../BLIS_exec/build/${CACHE_PROFILE} ${RISCV_SDK}/rootfs/buildroot_initramfs_sysroot/

  

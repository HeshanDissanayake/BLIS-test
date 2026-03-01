#!/usr/bin/env bash
set -e
BLIS_LIB_DIR=/opt/dev/blis
RISCV_SDK=/home/heshds/working_dir/cva6-sdk
IMG_DIR=/home/heshds/working_dir/regsw_tests/BLIS-test/Experimants/spike-normal/images


MC=$1
NC=$2
KC=$3


# check for library
CACHE_PROFILE="MC_${MC}_KC_${KC}_NC_${NC}"
if [ ! -d "${BLIS_LIB_DIR}/${CACHE_PROFILE}" ]; then
    echo "BLIS library ${CACHE_PROFILE} not found. Building..."
    ../util/build_lib.sh ${MC} ${NC} ${KC}
else
    echo "Using cached BLIS library ${BLIS_DIR}"
    # TODO: build the lib
fi

# Build the executable
make -C ../../../BLIS_exec CACHE_PROFILE=${CACHE_PROFILE}

# clean blis files in the rootfs
rm -f -r ${RISCV_SDK}/cva6-sdk-mods/home/blis
rm -f -r ${RISCV_SDK}/rootfs/home/blis
rm -f -r ${RISCV_SDK}/buildroot/output/target/home/blis

# copy it to the rootfs
mkdir -p "${RISCV_SDK}/cva6-sdk-mods/home/blis"
cp -r ../../../BLIS_exec/build/${CACHE_PROFILE} ${RISCV_SDK}/cva6-sdk-mods/home/blis/${CACHE_PROFILE}

# check for prebuilt linux image
if [ ! -f "${IMG_DIR}/${CACHE_PROFILE}.spike" ]; then
    echo "spike image ${CACHE_PROFILE}.spike not found. Building..."
    rm -rf install64
    make -C ${RISCV_SDK} rebuild
    cp install64/spike_fw_payload.elf "${IMG_DIR}/${CACHE_PROFILE}.spike"

else
    echo "already have spike image ${CACHE_PROFILE}.spike"
    # TODO: build the lib
fi


  

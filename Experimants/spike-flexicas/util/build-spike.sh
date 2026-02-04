#!/usr/bin/env bash
set -e

SPIKE_DIR=/home/heshds/working_dir/spike-flexicas/spike-flexicas
SPIKE_BUILD_DIR=../prebuilt_spikes

L1_SIZE=$1
L1_LW=$2
L1_ASC=$3

# dir="L1_${L1_SIZE}/LW_${L1_LW}/ASC_${L1_ASC}"
spike_config="L1_${L1_SIZE}_LW${L1_LW}_ASC${L1_ASC}"

# Create directories
mkdir -p "${SPIKE_BUILD_DIR}/${spike_config}"

# If spike binary is not already built, build it
if [ ! -f "${SPIKE_BUILD_DIR}/${spike_config}/spike" ]; then
    echo "Spike config ${spike_config} not found. Building..."

    (
        cd "${SPIKE_DIR}" || exit 1
        ./cache_exploration/scripts/build_spike_flexcas.sh \
            "${L1_SIZE}" "${L1_LW}" "${L1_ASC}"
    )

    # Save built binary into cache
    cp "${SPIKE_DIR}/build/spike" "${SPIKE_BUILD_DIR}/${spike_config}/spike"
    cp "${SPIKE_DIR}/build/libflexicas.so" "${SPIKE_BUILD_DIR}/${spike_config}/libflexicas.so"
    patchelf --set-rpath "${SPIKE_BUILD_DIR}/${spike_config}" "${SPIKE_BUILD_DIR}/${spike_config}/spike"

else
    echo "Using cached spike config ${spike_config}"
fi



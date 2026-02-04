#!/usr/bin/env bash
exp_dir=$1
RISCV_SDK=/home/heshds/working_dir/spike-flexicas/riscv-spike-sdk

# Safety check
if [[ ! -d "$exp_dir" ]]; then
    echo "Error: '$exp_dir' is not a directory" >&2
    exit 1
fi


cd "${exp_dir}" || exit 1

# clean the bbl rootfs
rm -r ${RISCV_SDK}/rootfs/buildroot_initramfs_sysroot/MC*

# build all the requried blis executables
cat config.json \
| python3 ../../Experiment_tools/expand_config.py -i MC,NC,KC\
| python3 ../../Experiment_tools/run_per_config.py ../util/build_exec.sh MC NC KC

# make bbl
make -C ${RISCV_SDK} bbl

# copy the bbl to the experiment dir
cp ${RISCV_SDK}/build/riscv-pk/bbl bbl
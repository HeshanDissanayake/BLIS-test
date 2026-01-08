#!/bin/bash
set -e

source ../config/blis/all-2
source ../config/parser.sh

MC=($(parse_list "$MC"))
NC=($(parse_list "$NC"))
KC=($(parse_list "$KC"))

pushd /home/heshds/working_dir/blis > /dev/null

# Debug: Print current directory and check for build.sh

for mc in "${MC[@]}"; do
  for nc in "${NC[@]}"; do
    for kc in "${KC[@]}"; do
      echo "========================================"
      echo "Running build: MC=${mc}, NC=${nc}, KC=${kc}"
      echo "========================================"

      ./build.sh -m ${mc} -n ${nc} -k ${kc}
    done
  done
done

popd > /dev/null

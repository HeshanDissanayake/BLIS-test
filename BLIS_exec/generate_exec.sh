#!/bin/bash
set -e

source ../config/blis/all-2
source ../config/parser.sh

MC=($(parse_list "$MC"))
NC=($(parse_list "$NC"))
KC=($(parse_list "$KC"))

for mc in "${MC[@]}"; do
  for nc in "${NC[@]}"; do
    for kc in "${KC[@]}"; do
      echo "========================================"
      echo "Running build: MC=${mc}, NC=${nc}, KC=${kc}"
      echo "========================================"

      make CACHE_PROFILE=MC_${mc}_KC_${kc}_NC_${nc}
    done
  done
done

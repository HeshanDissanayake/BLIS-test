#!/bin/bash
set -e

MC_VALUES=(16 32 64 96 128 256)

for MC in "${MC_VALUES[@]}"; do
  NC=$MC
  for KC in $(seq 64 64 640); do
    echo "========================================"
    echo "Running build: MC=${MC}, NC=${NC}, KC=${KC}"
    echo "========================================"

    make CACHE_PROFILE=MC_${MC}_KC_${KC}_NC_${NC}
  done
done

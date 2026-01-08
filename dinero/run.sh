#!/bin/bash
# Usage: ./run_dinero_matrix.sh

set -euo pipefail

BASE_DIR="trace"
PYTHON_SCRIPT="extract_missrate.py"

FLAGS="-l1-isize 8k \
    -l1-ibsize 16 \
    -l1-iassoc 2 \
    -l1-irepl l \
    -l1-ifetch d \
    -l1-dsize 640k \
    -l1-dbsize 16 \
    -l1-dassoc 1 \
    -l1-drepl l \
    -l1-dfetch d \
    -l1-dwalloc a \
    -l1-dwback a \
    -flushcount 10k \
    -stat-idcombine \
    -informat D"

for cache_cfg in "$BASE_DIR"/*; do
    [[ -d "$cache_cfg" ]] || continue

    cache_name=$(basename "$cache_cfg")
    csv_file="${cache_name}.csv"

    echo "Processing cache config: $cache_name"

    #
    # -------- Discover & sort register configs numerically --------
    #
    mapfile -t REG_CFGS < <(
        ls "$cache_cfg" \
        | awk -F'x' '{print $1}' \
        | sort -n \
        | awk '{print $1 "x" $1}'
    )

    #
    # -------- Write CSV header --------
    #
    echo -n "N" > "$csv_file"
    for reg in "${REG_CFGS[@]}"; do
        echo -n ",$reg" >> "$csv_file"
    done
    echo >> "$csv_file"

    #
    # -------- Discover & sort N values numerically --------
    #
    mapfile -t N_FILES < <(
        ls "$cache_cfg/${REG_CFGS[0]}"/*.log \
        | xargs -n1 basename \
        | sed 's/N\([0-9]\+\)\.log/\1/' \
        | sort -n \
        | awk '{print "N" $1 ".log"}'
    )

    #
    # -------- Fill CSV --------
    #
    for nfile in "${N_FILES[@]}"; do
        nlabel="${nfile%.log}"
        echo -n "$nlabel" >> "$csv_file"

        for reg in "${REG_CFGS[@]}"; do
            logfile="$cache_cfg/$reg/$nfile"

            if [[ -f "$logfile" ]]; then
                miss_rate=$(dineroIV $FLAGS < "$logfile" \
                            | python3 "$PYTHON_SCRIPT")
            else
                miss_rate="NA"
            fi

            echo -n ",$miss_rate" >> "$csv_file"
        done

        echo >> "$csv_file"
    done

    echo "  → wrote $csv_file"
done

echo "All cache configs processed."

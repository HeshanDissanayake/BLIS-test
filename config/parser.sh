parse_list() {
  local spec="$1"
  local out=()

  IFS=',' read -ra parts <<< "$spec"
  for p in "${parts[@]}"; do

    # Range with step: A-B:S
    if [[ "$p" =~ ^([0-9]+)-([0-9]+):([0-9]+)$ ]]; then
      local start=${BASH_REMATCH[1]}
      local end=${BASH_REMATCH[2]}
      local step=${BASH_REMATCH[3]}
      for ((i=start; i<=end; i+=step)); do
        out+=("$i")
      done

    # Range without step: A-B
    elif [[ "$p" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      local start=${BASH_REMATCH[1]}
      local end=${BASH_REMATCH[2]}
      for ((i=start; i<=end; i++)); do
        out+=("$i")
      done

    # Single value
    else
      out+=("$p")
    fi
  done

  echo "${out[@]}"
}
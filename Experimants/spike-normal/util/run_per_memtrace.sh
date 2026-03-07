echo "@ run_dinero_per_config.sh ---> Arguments: $@"
set -e

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --MC) MC="$2"; shift ;;
        --NC) NC="$2"; shift ;;
        --KC) KC="$2"; shift ;;
        --MR) MR="$2"; shift ;;
        --NR) NR="$2"; shift ;;
        --EXP_DIR) EXP_DIR="$2"; shift ;;
        --*) shift ;;  # ignore unknown named args
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if all parameters are set
if [ -z "$MC" ] || [ -z "$NC" ] || [ -z "$KC" ] || [ -z "$MR" ] || [ -z "$NR" ] || [ -z "$EXP_DIR" ]; then
    echo "Error: Missing required arguments. Usage: $0 --MC <val> --NC <val> --KC <val> --MR <val> --NR <val> --EXP_DIR <path>"
    exit 1
fi


ROOT=$(pwd)
EXP_TOOLS=${ROOT}/../../Experiment_tools
UTIL=${ROOT}/../util

# Run dinero for all the cache Configurations
CACHE_CONFIG="MC${MC}/KC${KC}/NC${NC}/MR${MR}/NR${NR}/"

cat config.json \
| python3 ${EXP_TOOLS}/expand_config.py -i L1_SIZE,L1_LW,L1_ASC \
| python3 ${EXP_TOOLS}/run_per_config.py ${UTIL}/get_data.py L1_SIZE L1_LW L1_ASC -a ${CACHE_CONFIG} -a ${EXP_DIR}/memtraces




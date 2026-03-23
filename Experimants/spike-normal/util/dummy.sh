echo "@ dummy.sh ---> Arguments: $@"

MC=$1
NC=$2
KC=$3
MR=$4
NR=$5

mkdir -p analysed_data/MC_${MC}/NC_${NC}/KC_${KC}/MR_${MR}/NR_${NR}
echo "{}" > analysed_data/MC_${MC}/NC_${NC}/KC_${KC}/MR_${MR}/NR_${NR}/avg.json


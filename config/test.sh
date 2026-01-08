source config/experiment-1
source config/parser.sh

# ----------------------------
# Expand values
# ----------------------------
MR=($(parse_list "$MR"))
MC=($(parse_list "$MC"))
KC=($(parse_list "$KC"))

# ----------------------------
# Print nicely
# ----------------------------
echo "MR:"
printf "  %s\n" "${MR[@]}"

echo
echo "MC:"
printf "  %s\n" "${MC[@]}"

echo
echo "KC:"
printf "  %s\n" "${KC[@]}"
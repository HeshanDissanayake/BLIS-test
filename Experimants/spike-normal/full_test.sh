# build BLIS and images form them
./build_linux.sh ${1}

# run spike and collect memtraces and split them into separate files
./run_memtrace.sh ${1}

# run dinero on the memtraces and collect the data in json files
./run_dinero.sh ${1}



# Dinero flags
FLAGS="-l1-isize 32k \
    -l1-ibsize 16 \
    -l1-iassoc 16 \
    -l1-irepl l \
    -l1-ifetch d \
    -l1-dsize 32k \
    -l1-dbsize 16 \
    -l1-dassoc 16 \
    -l1-drepl f \
    -l1-dfetch d \
    -l1-dwalloc a \
    -l1-dwback a \
    -l2-usize 256k \
    -l2-ubsize 64 \
    -l2-uassoc 8 \
    -l2-urepl f \
    -l2-ufetch d \
    -l2-uwalloc a \
    -l2-uwback a \
    -flushcount 10k \
    -stat-idcombine \
    -informat D"

# Run dinero and pipe to parser
dineroIV $FLAGS < "$1" 
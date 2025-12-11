# Toolchain
CC =  /opt/dev/riscv_linux_rv64g_regsw/bin/riscv64-unknown-linux-gnu-gcc
SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk
CFLAGS = -O2   -static
LDFLAGS =  -lblis -lpthread -lm

# BLIS_GENERIC = -I/opt/dev/blis/blis_generic/include/ -L/opt/dev/blis/blis_generic/lib/
BLIS_4x4 = -I/opt/dev/blis/blis_4x4/include/ -L/opt/dev/blis/blis_4x4/lib/
BLIS_8x8 = -I/opt/dev/blis/blis_8x8/include/ -L/opt/dev/blis/blis_8x8/lib/

# Target
# TARGET = gemm_blis_4x4 gemm_blis_8x8 
SRC = main.c

all: clean gemm_blis_4x4 gemm_blis_8x8

gemm_blis_4x4: $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_4x4) -o $@

gemm_blis_8x8: $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_8x8) -o $@


run-spike:
	$(SPIKE) $(PK) $(TARGET)  8 

clean:
	rm -f gemm_blis_4x4 gemm_blis_8x8

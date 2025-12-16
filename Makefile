# Toolchain
CC =  /opt/dev/riscv_linux_rv64g_regsw/bin/riscv64-unknown-linux-gnu-gcc
SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk
CFLAGS = -O2   -static
LDFLAGS =  -lblis -lpthread -lm


CACHE_PROFILE = MC_16_KC_120_NC_16
# CACHE_PROFILE = MC_320_KC_960_NC_4096

ROOT_LIB_PATH = /opt/dev/blis/$(CACHE_PROFILE)

# BLIS_GENERIC = -I/opt/dev/blis/blis_generic/include/ -L/opt/dev/blis/blis_generic/lib/
BLIS_4x4   = -I$(ROOT_LIB_PATH)/blis_4x4/include/ -L$(ROOT_LIB_PATH)/blis_4x4/lib/
BLIS_8x8   = -I$(ROOT_LIB_PATH)/blis_8x8/include/ -L$(ROOT_LIB_PATH)/blis_8x8/lib/
BLIS_16x16 = -I$(ROOT_LIB_PATH)/blis_16x16/include/ -L$(ROOT_LIB_PATH)/blis_16x16/lib/

# Target
# TARGET = gemm_blis_4x4 gemm_blis_8x8 
SRC = main.c

all: clean gemm_blis_4x4 gemm_blis_8x8 gemm_blis_16x16 print_params

gemm_blis_4x4: $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_4x4) -o $@

gemm_blis_8x8: $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_8x8) -o $@

gemm_blis_16x16: $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_16x16) -o $@

print_params: print_params.c
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_4x4) -o $@_4x4
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_8x8) -o $@_8x8
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_16x16) -o $@_16x16

run-spike:
	$(SPIKE) $(PK) $(TARGET)  8 

clean:
	rm -f gemm_blis_* print_params_*

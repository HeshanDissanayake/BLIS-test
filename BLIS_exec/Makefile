# Toolchain
CC = /opt/dev/riscv_linux_rv64g/bin/riscv64-unknown-linux-gnu-gcc
SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk
CFLAGS = -O2 -static
LDFLAGS = -lblis -lpthread -lm

# Cache profile
CACHE_PROFILE = None
# CACHE_PROFILE = MC_320_KC_960_NC_4096

ROOT_LIB_PATH = /opt/dev/blis/$(CACHE_PROFILE)

BLIS_4x4   = -I$(ROOT_LIB_PATH)/blis_4x4/include/   -L$(ROOT_LIB_PATH)/blis_4x4/lib/
BLIS_8x8   = -I$(ROOT_LIB_PATH)/blis_8x8/include/   -L$(ROOT_LIB_PATH)/blis_8x8/lib/
BLIS_16x16 = -I$(ROOT_LIB_PATH)/blis_16x16/include/ -L$(ROOT_LIB_PATH)/blis_16x16/lib/

# Sources
SRC = main.c

# Build directory
BUILD_DIR = build/$(CACHE_PROFILE)

# Targets
BIN_4x4   = $(BUILD_DIR)/gemm_blis_4x4
BIN_8x8   = $(BUILD_DIR)/gemm_blis_8x8
BIN_16x16 = $(BUILD_DIR)/gemm_blis_16x16

PARAM_4x4   = $(BUILD_DIR)/print_params_4x4
PARAM_8x8   = $(BUILD_DIR)/print_params_8x8
PARAM_16x16 = $(BUILD_DIR)/print_params_16x16

all: clean $(BIN_4x4) $(BIN_8x8) $(BIN_16x16) 

# Ensure build directory exists
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BIN_4x4): $(SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_4x4) -o $@

$(BIN_8x8): $(SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_8x8) -o $@

$(BIN_16x16): $(SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_16x16) -o $@

$(PARAM_4x4): print_params.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_4x4) -o $@

$(PARAM_8x8): print_params.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_8x8) -o $@

$(PARAM_16x16): print_params.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_16x16) -o $@

run-spike:
	$(SPIKE) $(PK) $(BIN_4x4) 8

clean:
	rm -rf $(BUILD_DIR)

clean_are_you_sure:
	rm -r build/*



# Toolchain
CC = /opt/dev/riscv_linux_rv64g/bin/riscv64-unknown-linux-gnu-gcc
SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk
CFLAGS = -O2 -static
LDFLAGS = -lblis -lpthread -lm

# Cache profile (e.g. MC_320_KC_960_NC_4096)
CACHE_PROFILE = None

# Register size (e.g. 4x4, 8x8, 16x16)
REG_SIZE =

ROOT_LIB_PATH = /opt/dev/blis/$(CACHE_PROFILE)
BLIS_FLAGS = -I$(ROOT_LIB_PATH)/blis_$(REG_SIZE)/include/ -L$(ROOT_LIB_PATH)/blis_$(REG_SIZE)/lib/

# Sources
SRC = main.c

# Build directory
BUILD_DIR = build/$(CACHE_PROFILE)

# Targets
BIN   = $(BUILD_DIR)/gemm_blis_$(REG_SIZE)
PARAM = $(BUILD_DIR)/print_params_$(REG_SIZE)

all: clean $(BIN)

# Ensure build directory exists
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BIN): $(SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) $(BLIS_FLAGS) -o $@

$(PARAM): print_params.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) print_params.c $(LDFLAGS) $(BLIS_FLAGS) -o $@

run-spike:
	$(SPIKE) $(PK) $(BIN) 8

clean:
	rm -rf $(BUILD_DIR)

clean_are_you_sure:
	rm -r build/*



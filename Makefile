# Toolchain
CC =  /opt/dev/riscv_linux_rv64g_regsw/bin/riscv64-unknown-linux-gnu-gcc
SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk
CFLAGS = -O2  -I/opt/dev/blis/include/ -static
LDFLAGS = -L/opt/dev/blis/lib/ -lblis -lpthread -lm

# Target
TARGET = gemm_riscv_generic
SRC = main.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) -o $(TARGET)

run-spike:
	$(SPIKE) $(PK) $(TARGET)

clean:
	rm -f $(TARGET)

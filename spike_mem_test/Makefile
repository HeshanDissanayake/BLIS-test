# Toolchain
CC = /opt/dev/riscv_linux_rv64g_regsw/bin/riscv64-unknown-linux-gnu-gcc
SPIKE=/home/heshds/working_dir/cva6-sdk/riscv-isa-sim/build/spike
OBJDUMP=/opt/dev/riscv_linux_rv64g_regsw/bin/riscv64-unknown-linux-gnu-objdump
# SPIKE = /home/heshds/working_dir/cva6-sdk/install64/bin/spike
# SPIKE =  /home/heshds/working_dir/riscv-isa-sim/build/spike
PK = /home/heshds/working_dir/riscv-pk_64/build/pk

CFLAGS  = -static 

TARGET = test
SRC    = main.c

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $^ -o $@

dump: $(TARGET)
	$(OBJDUMP) -d $(TARGET) > $(TARGET).dump

run: $(TARGET)
	$(SPIKE) --memtrace memtrace $(PK) $(TARGET) > log

clean:
	rm -f $(TARGET) $(TARGET).dump
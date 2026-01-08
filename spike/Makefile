SPIKE=/home/heshds/working_dir/cva6-sdk/riscv-isa-sim/build/spike
SDK_PATH=/home/heshds/working_dir/cva6-sdk
PK=/home/heshds/working_dir/riscv-pk_64/build/pk
EXEC_DIR=/home/heshds/working_dir/regsw_tests/BLIS-test/BLIS_exec/build

CONFIG=None

rebuild-n-spike:
	
	# @(cd run && ./generate_run.sh $(CONFIG)) 
	# cp -r $(EXEC_DIR)/$(CONFIG)/* $(SDK_PATH)/cva6-sdk-mods/home/blis
	# cp run/run_static.sh $(SDK_PATH)/cva6-sdk-mods/home/blis
	# echo $(CONFIG) > $(SDK_PATH)/cva6-sdk-mods/home/blis/config.txt

	rm -r install64
	make -C $(SDK_PATH) rebuild
	$(SPIKE) --memtrace memtraces/memtrace_$(CONFIG) install64/spike_fw_payload.elf

spike:
	$(SPIKE) --memtrace memtraces/memtrace_$(CONFIG) install64/spike_fw_payload.elf

spike-pk: $(TARGET)
	$(SPIKE) --memtrace memtrace $(PK) /home/heshds/working_dir/regsw_tests/BLIS-test/BLIS_exec/build/MC_32_KC_64_NC_32/gemm_blis_4x4 8 8 8
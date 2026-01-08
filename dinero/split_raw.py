import sys
import os
import shutil
from pathlib import Path


import os

def split_log_stream(input_file, output_filenames):
    out_index = -1          # <-- start before first file
    current_out = None

    file_size = os.path.getsize(input_file)
    processed_bytes = 0
    last_percent = -1

    with open(input_file, "r") as f:
        for line in f:
            processed_bytes += len(line.encode("utf-8"))

            if line.strip() == "LOG MARKER":
                if current_out is not None:
                    current_out.close()
                    current_out = None

                out_index += 1
                if out_index >= len(output_filenames):
                    break
                continue

            # Ignore data before first marker (safety)
            if out_index < 0:
                continue

            if current_out is None:
                current_out = open(output_filenames[out_index], "w")

            current_out.write(line)

            percent = int(processed_bytes / file_size * 100)
            if percent != last_percent:
                bar_len = 50
                filled_len = int(bar_len * percent / 100)
                bar = "#" * filled_len + "-" * (bar_len - filled_len)
                print(f"\rProgress: |{bar}| {percent}% ", end="", flush=True)
                last_percent = percent

    if current_out is not None:
        current_out.close()

    print("\nDone.")


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print(f"Usage: python {sys.argv[0]} <input_log_file>")
    #     sys.exit(1)

    
    MR = [4,8,16]
    MC = [32, 64, 96, 128, 256]
    NC = MC
    KC = [64]
    N = [16 ,32 ,48 ,64 ,80 ,96 ,112 ,128 ,144 ,160 ,176 ,192 ,208 ,224 ,240 ,256 ,512]



    # Generate output filenames
    for mc in MC:
        nc = mc
        for kc in KC:
            config = f"MC_{mc}_KC_{kc}_NC_{nc}"
            output_filenames = []
            input_file = f"/home/heshds/working_dir/regsw_tests/BLIS-test/spike/memtraces/memtrace_{config}"
            cache_config = f"MC{mc}_KC{kc}_NC{nc}"
            for mr in MR:
                register_config = f"{mr}x{mr}"
                path = Path(f"trace/{cache_config}/{register_config}")
                path.mkdir(parents=True, exist_ok=True)
                for n in N:
                    output_filenames.append(f"trace/{cache_config}/{register_config}/N{n}.log")
        print(f"Processing input file: {input_file}")
        split_log_stream(input_file, output_filenames)

                    
    # shutil.os.makedirs("trace", exist_ok=True)


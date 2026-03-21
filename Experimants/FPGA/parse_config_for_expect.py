import sys, json

try:
    # Read from stdin (which will be the output of expand_config.py)
    data = json.load(sys.stdin)
    
    if 'configs' not in data:
        sys.exit(0)

    for c in data['configs']:
        # Construct filename and outfile
        # format: MC_4096_KC_32_NC_4096/gemm_blis_4x4
        # outfile: MC_4096_KC_32_NC_4096_gemm_blis_4x4
        mc = c.get('MC', '0')
        kc = c.get('KC', '0')
        nc = c.get('NC', '0')
        mr = c.get('MR', '0')
        nr = c.get('NR', '0')
        
        filename = f"MC_{mc}_KC_{kc}_NC_{nc}/gemm_blis_{mr}x{nr}"
        outfile = f"MC_{mc}_KC_{kc}_NC_{nc}_gemm_blis_{mr}x{nr}"
        
        print(f"{filename} {outfile}")

except Exception as e:
    sys.stderr.write(f"Error parsing json: {e}\n")
    sys.exit(1)

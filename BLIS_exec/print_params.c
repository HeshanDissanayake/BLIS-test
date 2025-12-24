#include <stdio.h>
#include "blis.h"

int main(void)
{
    // Declare and initialize BLIS context
    cntx_t cntx;
    bli_cntx_init_rv64i_ref(&cntx);   // Use reference RV64I context
                                       // or remove this line to use default context

    // Query default block sizes for double-precision
    dim_t MR = bli_blksz_get_def(BLIS_DOUBLE, bli_cntx_get_blksz(BLIS_MR, &cntx));
    dim_t NR = bli_blksz_get_def(BLIS_DOUBLE, bli_cntx_get_blksz(BLIS_NR, &cntx));
    dim_t MC = bli_blksz_get_def(BLIS_DOUBLE, bli_cntx_get_blksz(BLIS_MC, &cntx));
    dim_t KC = bli_blksz_get_def(BLIS_DOUBLE, bli_cntx_get_blksz(BLIS_KC, &cntx));
    dim_t NC = bli_blksz_get_def(BLIS_DOUBLE, bli_cntx_get_blksz(BLIS_NC, &cntx));

    // Print block sizes
    printf("MR=%ld NR=%ld MC=%ld KC=%ld NC=%ld\n",
           (long)MR, (long)NR, (long)MC, (long)KC, (long)NC);

    // Finalize BLIS (optional)
    bli_finalize();

    return 0;
}

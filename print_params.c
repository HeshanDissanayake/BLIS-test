cntx_t cntx;
bli_cntx_init_rv64i_ref(&cntx);   // or any real arch init you have
                                        // or remove this line to use default

dim_t MR = bli_blksz_get_def( BLIS_DOUBLE, bli_cntx_get_blksz( BLIS_MR, &cntx ) );
dim_t NR = bli_blksz_get_def( BLIS_DOUBLE, bli_cntx_get_blksz( BLIS_NR, &cntx ) );
dim_t MC = bli_blksz_get_def( BLIS_DOUBLE, bli_cntx_get_blksz( BLIS_MC, &cntx ) );
dim_t KC = bli_blksz_get_def( BLIS_DOUBLE, bli_cntx_get_blksz( BLIS_KC, &cntx ) );
dim_t NC = bli_blksz_get_def( BLIS_DOUBLE, bli_cntx_get_blksz( BLIS_NC, &cntx ) );

printf("MR=%ld NR=%ld MC=%ld KC=%ld NC=%ld\n", MR, NR, MC, KC, NC);
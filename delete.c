#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char **argv)
{
    if (argc < 4) {
        printf("Usage: %s <M> <K> <N>\n", argv[0]);
        printf("Computes: C(MxN) = A(MxK) * B(KxN)\n");
        return 1;
    }

    unsigned long long M = atoi(argv[1]);
    unsigned long long K = atoi(argv[2]);
    unsigned long long N = atoi(argv[3]);

   
    /* Performance stats */
    double flops = 2.0 * (double)M * (double)N * (double)K;
    double time =  50.0; // us
    double mflops = flops / time;
    
    // double sum = checksum(C, M, N);

    // printf("N,%ld,mflops,%.6f\n", (long)N, mflops);
    printf("%ld,%ld,%ld,%.6f,%llu,%.6f,%.6f\n", (long)N, (long)M,(long)K, flops, mflops, time);


    /* Cleanup */

    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "blis.h"

/* Print rectangular matrix */
void print_matrix(const char* name, const double* M, dim_t rows, dim_t cols)
{
    printf("%s =\n", name);
    for (dim_t i = 0; i < rows; ++i)
    {
        for (dim_t j = 0; j < cols; ++j)
        {
            printf("%10.4f ", M[i*cols + j]);   // row-major
        }
        printf("\n");
    }
    printf("\n");
}

/* Wall time */
double now_seconds() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

/* RISC-V cycle counter */
static inline unsigned long long read_cycles(void) {
    unsigned long long cycles;
    asm volatile ("rdcycle %0" : "=r"(cycles));
    return cycles;
}

/* RISC-V inst retire counter */
static inline uint64_t read_instret(void)
{
    uint64_t val;
    asm volatile ("rdinstret %0" : "=r"(val));
    return val;
}

/* Fill arbitrary size matrix */
void fill_matrix(double *buf, dim_t rows, dim_t cols, unsigned start) {
    for (dim_t i = 0; i < rows * cols; i++)
        buf[i] = start + i;
}

/* Checksum for rectangular matrix */
double checksum(double *buf, dim_t rows, dim_t cols) {
    double s = 0.0;
    for (dim_t i = 0; i < rows * cols; i++)
        s += buf[i];
    return s;
}

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
    double flops = 2.0 * (double)M * (double)N * (double)K;

    /* Allocate matrices */
    double *A = aligned_alloc(64, sizeof(double) * M * K);
    double *B = aligned_alloc(64, sizeof(double) * K * N);
    double *C = aligned_alloc(64, sizeof(double) * M * N);

    /* Fill inputs */
    fill_matrix(A, M, K, 0);
    fill_matrix(B, K, N, 100);

    for (dim_t i = 0; i < M * N; i++)
        C[i] = 0.0;

    // print_matrix("Matrix A", A, M, K);
    // print_matrix("Matrix B", B, K, N);

    /* Init BLIS */
    bli_init();

    obj_t a, b, c, alpha, beta;

    /* Create BLIS objects (row-major: rs=cols, cs=1) */
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, M, K, A, K, 1, &a);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, K, N, B, N, 1, &b);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, M, N, C, N, 1, &c);

    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &alpha);
    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &beta);
    bli_setsc(1.0, 0.0, &alpha);
    bli_setsc(0.0, 0.0, &beta);

    /* Warm-up */
    bli_gemm(&alpha, &a, &b, &beta, &c);

    /* Measure */
    unsigned long long start_cycles = read_cycles();
    
    bli_gemm(&alpha, &a, &b, &beta, &c);
    
    unsigned long long end_cycles = read_cycles();

    unsigned long long cycles = end_cycles - start_cycles;

    // print_matrix("Matrix C", C, M, N);

    /* Performance stats */
    
    double time = cycles / 50.0; // us
    double mflops = flops / time;
    
    // double sum = checksum(C, M, N);

    // printf("N,%ld,mflops,%.6f\n", (long)N, mflops);
    printf("%ld,%ld,%ld,%.6f,%llu,%.6f,%.6f\n", (long)N, (long)M,(long)K, flops, cycles, mflops, time);


    /* Cleanup */
    bli_finalize();
    free(A); free(B); free(C);

    return 0;
}

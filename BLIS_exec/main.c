#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <stdbool.h>
#include "blis.h"

#define CSR_MEM_DUMP 0x815
#define CSR_MEM_LOG_MARKER 0x816

static inline void csr_mem_dump_set_bits(int val)
{
    asm volatile (
        "csrw %0, %1"
        :
        : "i"(CSR_MEM_DUMP), "r"(val)
        : 
    );
}

static inline void csr_mem_log_marker(int val)
{
    asm volatile (
        "csrw %0, %1"
        :
        : "i"(CSR_MEM_LOG_MARKER), "r"(val)
        : 
    );
}

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
        printf("Usage: %s <M> <K> <N> [-m]\n", argv[0]);
        printf("Computes: C(MxN) = A(MxK) * B(KxN)\n");
        printf("  -m: Enable memory dump\n");
        return 1;
    }

    // Check for -m flag
    bool enable_mem_dump = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0) {
            enable_mem_dump = true;
            break;
        }
    }

    // Parse matrix dimensions, skipping the -m flag if present
    int args_found = 0;
    unsigned long long dims[3];
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0) continue;
        if (args_found < 3) {
            dims[args_found++] = atoi(argv[i]);
        }
    }
    
    if (args_found < 3) {
        printf("Error: Missing matrix dimensions.\n");
        return 1;
    }

    unsigned long long M = dims[0];
    unsigned long long K = dims[1];
    unsigned long long N = dims[2];
    double flops = 2.0 * (double)M * (double)N * (double)K;

    /* Allocate matrices */
    double *A = aligned_alloc(64, sizeof(double) * M * K);
    double *B = aligned_alloc(64, sizeof(double) * K * N);
    double *C = aligned_alloc(64, sizeof(double) * M * N);

    /* Fill inputs */
    // fill_matrix(A, M, K, 0);
    // fill_matrix(B, K, N, 100);

    // for (dim_t i = 0; i < M * N; i++)
    //     C[i] = 0.0;

    // print_matrix("Matrix A", A, M, K);
    // print_matrix("Matrix B", B, K, N);

    /* Init BLIS */
    bli_init();
    printf("inited\n");
    obj_t a, b, c, alpha, beta;

    /* Create BLIS objects (row-major: rs=cols, cs=1) */
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, M, K, A, K, 1, &a);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, K, N, B, N, 1, &b);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, M, N, C, N, 1, &c);

    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &alpha);
    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &beta);
    bli_setsc(1.0, 0.0, &alpha);
    bli_setsc(0.0, 0.0, &beta);
    printf("obj_created\n");
    /* Warm-up */
    // bli_gemm(&alpha, &a, &b, &beta, &c);

    /* Measure */
    unsigned long long start_cycles = read_cycles();
    unsigned long long start_instret = read_instret();

    if (enable_mem_dump) {
        csr_mem_dump_set_bits(1);
    }
    
    bli_gemm(&alpha, &a, &b, &beta, &c);
    printf("gemm end\n");
    
    // Memory dump end marker
    if (enable_mem_dump) {
        csr_mem_log_marker(0);
        csr_mem_dump_set_bits(0);
    }
    
    unsigned long long end_cycles = read_cycles();
    unsigned long long end_instret = read_instret();

    unsigned long long cycles = end_cycles - start_cycles;
    unsigned long long instret = end_instret - start_instret;

    // print_matrix("Matrix C", C, M, N);

    /* Performance stats */
    
    double time = cycles / 50.0; // us
    double mflops = flops / time;
    
    // double sum = checksum(C, M, N);

    printf("N,%ld,cycles,%llu,instret,%llu\n", (long)N, cycles, instret);
    printf("done\n");


    /* Cleanup */
    bli_finalize();
    free(A); free(B); free(C);

    return 0;
}

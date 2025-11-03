#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "blis.h"

// Get current wall clock in seconds
double now_seconds() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

// Read RISC-V cycle counter
static inline unsigned long long read_cycles(void) {
    unsigned long long cycles;
    asm volatile ("rdcycle %0" : "=r"(cycles));
    return cycles;
}

// Fill a square matrix with random values
void rand_matrix(double *buf, dim_t n, unsigned seed) {
    srand(seed);
    for (dim_t i = 0; i < n * n; i++)
        buf[i] = ((double)rand() / RAND_MAX) - 0.5;
}

// Compute simple checksum of matrix
double checksum(double *buf, dim_t n) {
    double s = 0.0;
    for (dim_t i = 0; i < n * n; i++) s += buf[i];
    return s;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        printf("Usage: %s <matrix_size>\n", argv[0]);
        return 1;
    }

    dim_t N = atoi(argv[1]);  // matrix size N x N

    // Allocate aligned buffers
    double *A = aligned_alloc(64, sizeof(double) * N * N);
    double *B = aligned_alloc(64, sizeof(double) * N * N);
    double *C = aligned_alloc(64, sizeof(double) * N * N);

    rand_matrix(A, N, 1234);
    rand_matrix(B, N, 5678);
    for (dim_t i = 0; i < N * N; i++) C[i] = 0.0;

    // Initialize BLIS
    bli_init();

    // Create BLIS objects
    obj_t a, b, c, alpha, beta;
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, A, 1, N, &a);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, B, 1, N, &b);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, C, 1, N, &c);

    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &alpha);
    bli_obj_create(BLIS_DOUBLE, 1, 1, 0, 0, &beta);
    bli_setsc(1.0, 0.0, &alpha);
    bli_setsc(0.0, 0.0, &beta);

    // Warmup (to preload cache)
    bli_gemm(&alpha, &a, &b, &beta, &c);

    // Time and cycle count measurement
    unsigned long long start_cycles = read_cycles();
    double t0 = now_seconds();
    bli_gemm(&alpha, &a, &b, &beta, &c);
    double t1 = now_seconds();
    unsigned long long end_cycles = read_cycles();

    double elapsed = t1 - t0;
    unsigned long long cycles = end_cycles - start_cycles;

    // Derived metrics
    double gflops = 2.0 * N * N * N / (elapsed * 1e6);
    double sum = checksum(C, N);
    double freq_hz = cycles / elapsed;
    double freq_mhz = freq_hz / 1e6;

    printf("N=%ld, time(s)=%.6f, cycles=%llu, freq(MHz)=%.2f, MFLOPS=%.5f, checksum=%.6f\n",
           (long)N, elapsed, cycles, freq_mhz, gflops, sum);

    // Finalize
    bli_finalize();
    free(A); free(B); free(C);

    return 0;
}

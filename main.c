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

// Fill a square matrix with random values
void rand_matrix(double *buf, dim_t n, unsigned seed) {
    srand(seed);
    for (dim_t i = 0; i < n*n; i++)
        buf[i] = ((double)rand() / RAND_MAX) - 0.5;
}

// Compute simple checksum of matrix
double checksum(double *buf, dim_t n) {
    double s = 0.0;
    for (dim_t i=0; i<n*n; i++) s += buf[i];
    return s;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        printf("Usage: %s <matrix_size>\n", argv[0]);
        return 1;
    }

    dim_t N = atoi(argv[1]);  // matrix size N x N

    // Allocate raw buffers (column-major)
    double *A = aligned_alloc(64, sizeof(double)*N*N);
    double *B = aligned_alloc(64, sizeof(double)*N*N);
    double *C = aligned_alloc(64, sizeof(double)*N*N);

    rand_matrix(A, N, 1234);
    rand_matrix(B, N, 5678);
    for (dim_t i=0;i<N*N;i++) C[i]=0.0;

    // Initialize BLIS
    bli_init();

    // Create objects
    obj_t a, b, c, alpha, beta;
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, A, 1, N, &a);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, B, 1, N, &b);
    bli_obj_create_with_attached_buffer(BLIS_DOUBLE, N, N, C, 1, N, &c);

    // Scalars
    bli_obj_create(BLIS_DOUBLE, 1,1,0,0,&alpha);
    bli_obj_create(BLIS_DOUBLE, 1,1,0,0,&beta);
    bli_setsc(1.0,0.0,&alpha);
    bli_setsc(0.0,0.0,&beta);

    // Warmup
    bli_gemm(&alpha, &a, &b, &beta, &c);

    // Timing
    double t0 = now_seconds();
    bli_gemm(&alpha, &a, &b, &beta, &c);
    double t1 = now_seconds();
    double elapsed = t1 - t0;

    // Compute GFLOPS: 2*N^3 / time (seconds)
    double gflops = 2.0 * N * N * N / (elapsed * 1e9);

    // Checksum
    double sum = checksum(C, N);

    printf("N=%ld, time=%.6f s, GFLOPS=%.2f, checksum=%.6f\n",
           (long)N, elapsed, gflops, sum);

    // Finalize
    bli_finalize();
    free(A); free(B); free(C);

    return 0;
}

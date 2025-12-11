#include <stdio.h>
#include <stdlib.h>
#include <time.h>


void print_matrix(const char* name, const double* M, int N)
{
    printf("%s =\n", name);
    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            printf("%10.4f ", M[i*N + j]);   // row-major indexing
        }
        printf("\n");
    }
    printf("\n");
}



// Fill a square matrix with random values
void rand_matrix(double *buf, int n, unsigned seed) {
    srand(seed);
    for (int i = 0; i < n * n; i++)
        buf[i] = ((double)rand() / RAND_MAX) - 0.5;
}

void fill_matrix(double *buf, int n, unsigned start) {
    for (int i = 0; i < n * n; i++)
        buf[i] = start + i;
}

// Compute simple checksum of matrix
double checksum(double *buf, int n) {
    double s = 0.0;
    for (int i = 0; i < n * n; i++) s += buf[i];
    return s;
}

// Matrix multiplication: C = A * B
void matmul(const double *A, const double *B, double *C, int N)
{
    for (int i = 0; i < N; i++)
    {
        for (int j = 0; j < N; j++)
        {
            double sum = 0.0;
            for (int k = 0; k < N; k++)
            {
                sum += A[i*N + k] * B[k*N + j];
            }
            C[i*N + j] = sum;
        }
    }
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        printf("Usage: %s <matrix_size>\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);  // matrix size N x N

    // Allocate aligned buffers
    double *A = aligned_alloc(64, sizeof(double) * N * N);
    double *B = aligned_alloc(64, sizeof(double) * N * N);
    double *C = aligned_alloc(64, sizeof(double) * N * N);

    // rand_matrix(A, N, 1234);
    // rand_matrix(B, N, 5678);

    fill_matrix(A, N, 0);
    fill_matrix(B, N, 100);

    print_matrix("Matrix A", A, N);
    print_matrix("Matrix B", B, N);
    
    for (int i = 0; i < N * N; i++) C[i] = 0.0;

    matmul(A, B, C, N);


    print_matrix("Matrix C", C, N);
    
    double sum = checksum(C, N);
  

    printf("checksum=%.6f\n",
           sum);

    free(A); free(B); free(C);

    return 0;
}

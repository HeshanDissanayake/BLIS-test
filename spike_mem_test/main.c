#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define CSR_MEM_DUMP 0x815
#define CSR_MEM_LOG_MARKER 0x816



static inline void csr_mem_dump_set_bits(unsigned long mask)
{
    asm volatile ("csrrs x0, %0, %1"
                  :
                  : "i"(CSR_MEM_DUMP), "r"(mask)
                  : "memory");
}

static inline void csr_mem_log_marker(unsigned long mask)
{
    asm volatile ("csrrs x0, %0, %1"
                  :
                  : "i"(CSR_MEM_LOG_MARKER), "r"(mask)
                  : "memory");
}


int main(void)
{   
    csr_mem_log_marker(0);
    csr_mem_dump_set_bits(1);
    int arr[20];

    /* Seed the random number generator */
    srand((unsigned int)time(NULL));

    /* Initialize array with random values */
    for (int i = 0; i < 20; i++) {
        arr[i] = rand() % 100;  // random number between 0 and 99
    }

    /* Print the array */
    printf("Array contents:\n");
    for (int i = 0; i < 20; i++) {
        printf("arr[%2d] = %d\n", i, arr[i]);
    }

    csr_mem_log_marker(0);
    csr_mem_dump_set_bits(0);

    return 0;
}

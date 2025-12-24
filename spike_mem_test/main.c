#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
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

    return 0;
}

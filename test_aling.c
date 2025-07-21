#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 10000000

// Aligned struct (naturally aligned by compiler)
struct AlignedStruct {
    int a;
    char b;
    double c;
} __attribute__((aligned(8)));

// Unaligned struct (packed to minimize padding)
struct UnalignedStruct {
    int a;
    char b;
    double c;
} __attribute__((packed));

// Function to simulate work with structs
void process_structs(void *data, size_t count, const char *type) {
    clock_t start = clock();
    volatile int sum = 0; // Volatile to prevent optimization
    for (size_t i = 0; i < count; i++) {
        if (type[0] == 'A') {
            struct AlignedStruct *s = (struct AlignedStruct *)data + i;
            sum += s->a + s->b + (int)s->c;
        } else {
            struct UnalignedStruct *s = (struct UnalignedStruct *)data + i;
            sum += s->a + s->b + (int)s->c;
        }
    }
    clock_t end = clock();
    double time_taken = (double)(end - start) / CLOCKS_PER_SEC * 1000; // in milliseconds
    printf("Time for %s structs: %.2f ms\n", type, time_taken);
}

int main() {
    // Allocate memory for arrays of structs
    struct AlignedStruct *aligned_data = malloc(SIZE * sizeof(struct AlignedStruct));
    struct UnalignedStruct *unaligned_data = malloc(SIZE * sizeof(struct UnalignedStruct));

    // Initialize data (simple values for consistency)
    for (size_t i = 0; i < SIZE; i++) {
        aligned_data[i].a = i;
        aligned_data[i].b = i % 128;
        aligned_data[i].c = i * 1.5;
        unaligned_data[i].a = i;
        unaligned_data[i].b = i % 128;
        unaligned_data[i].c = i * 1.5;
    }

    // Run performance test
    printf("Running performance test with %zu iterations...\n", SIZE);
    process_structs(aligned_data, SIZE, "Aligned");
    process_structs(unaligned_data, SIZE, "Unaligned");

    // Free memory
    free(aligned_data);
    free(unaligned_data);

    return 0;
}

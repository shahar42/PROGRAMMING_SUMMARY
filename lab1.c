#include <stdio.h> /* For printf */
#include <stdlib.h> /* For malloc, free */

/* Define a structure */
typedef struct MyStruct
{
    int data;
    /* other members */
} MyStruct_t;

/* "Constructor" equivalent: an initialization function */
void MyStruct_Init(MyStruct_t *obj_ptr, int initial_data)
{
    if (obj_ptr == NULL)
    {
        /* Handle error: cannot initialize a NULL pointer */
        return;
    }
    obj_ptr->data = initial_data;
    printf("MyStruct initialized with data: %d\n", obj_ptr->data);
}

/* "Destructor" equivalent: a cleanup function */
void MyStruct_Destroy(MyStruct_t *obj_ptr)
{
    if (obj_ptr == NULL)
    {
        /* Nothing to destroy for a NULL pointer */
        return;
    }
    printf("MyStruct resources cleaned up (data was: %d)\n", obj_ptr->data);
    /* In a more complex struct, you would free any internal malloc'd memory here */
}


int main(int argc, char* argv[])
{
    MyStruct_t stack_obj; /* Declare a struct on the stack */
    MyStruct_t *heap_obj; /* Declare a pointer for a heap-allocated struct */

    printf("Lab 1 started\n");

    /* Using the "constructor" for a stack-allocated struct */
    MyStruct_Init(&stack_obj, 100);

    /* Using the "constructor" for a heap-allocated struct */
    heap_obj = (MyStruct_t *)malloc(sizeof(MyStruct_t));
    if (heap_obj == NULL)
    {
        perror("Failed to allocate heap_obj");
        return 1;
    }
    MyStruct_Init(heap_obj, 200);

    /* ... do something with stack_obj and heap_obj ... */

    /* Using the "destructor" for the heap-allocated struct */
    MyStruct_Destroy(heap_obj);
    free(heap_obj); /* Free the memory allocated by malloc */
    heap_obj = NULL; /* Good practice to nullify freed pointers */

    /* The stack_obj automatically goes out of scope here.
     * You should explicitly call MyStruct_Destroy for it too if it has resources. */
    MyStruct_Destroy(&stack_obj);

    return 0;
}

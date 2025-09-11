#include <stdio.h>
#include <pthread.h>

int balance = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

typedef struct Deposit_info {
    int deposit_count;
    int last_deposit;
} info_t;

void add(int num, info_t* user) {
    pthread_mutex_lock(&mutex);
    balance += num;
    pthread_mutex_unlock(&mutex);
    
    ++(user->deposit_count);
    user->last_deposit = num;
}

void* thread_function(void* arg) {
    info_t* user = (info_t*)arg;
    
    // Make 5 deposits of $10 each
    for (int i = 0; i < 5; i++) {
        add(10, user);
        printf("Thread deposited $10, Balance: $%d, User deposits: %d\n", 
               balance, user->deposit_count);
    }
    
    return NULL;
}

int main() {
    pthread_t thread1, thread2;
    info_t user1 = {0, 0};
    info_t user2 = {0, 0};
    
    printf("Starting balance: $%d\n", balance);
    
    pthread_create(&thread1, NULL, thread_function, &user1);
    pthread_create(&thread2, NULL, thread_function, &user2);
    
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    
    printf("\nFinal Results:\n");
    printf("Balance: $%d\n", balance);
    printf("User 1 - Deposits: %d, Last: $%d\n", user1.deposit_count, user1.last_deposit);
    printf("User 2 - Deposits: %d, Last: $%d\n", user2.deposit_count, user2.last_deposit);
    
    pthread_mutex_destroy(&mutex);
    return 0;
}
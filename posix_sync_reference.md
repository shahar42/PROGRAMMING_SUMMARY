# POSIX Synchronization Primitives Reference

## POSIX Semaphores

| Function | Syntax | Description |
|----------|--------|-------------|
| **sem_init** | `int sem_init(sem_t *sem, int pshared, unsigned int value)` | Initialize unnamed semaphore |
| **sem_destroy** | `int sem_destroy(sem_t *sem)` | Destroy unnamed semaphore |
| **sem_wait** | `int sem_wait(sem_t *sem)` | Lock semaphore (blocking) |
| **sem_trywait** | `int sem_trywait(sem_t *sem)` | Try to lock semaphore (non-blocking) |
| **sem_timedwait** | `int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout)` | Lock semaphore with timeout |
| **sem_post** | `int sem_post(sem_t *sem)` | Unlock semaphore |
| **sem_getvalue** | `int sem_getvalue(sem_t *sem, int *sval)` | Get semaphore value |

### Named Semaphores

| Function | Syntax | Description |
|----------|--------|-------------|
| **sem_open** | `sem_t *sem_open(const char *name, int oflag, ...)` | Open/create named semaphore |
| **sem_close** | `int sem_close(sem_t *sem)` | Close named semaphore |
| **sem_unlink** | `int sem_unlink(const char *name)` | Remove named semaphore |

## POSIX Mutexes

| Function | Syntax | Description |
|----------|--------|-------------|
| **pthread_mutex_init** | `int pthread_mutex_init(pthread_mutex_t *mutex, const pthread_mutexattr_t *attr)` | Initialize mutex |
| **pthread_mutex_destroy** | `int pthread_mutex_destroy(pthread_mutex_t *mutex)` | Destroy mutex |
| **pthread_mutex_lock** | `int pthread_mutex_lock(pthread_mutex_t *mutex)` | Lock mutex (blocking) |
| **pthread_mutex_trylock** | `int pthread_mutex_trylock(pthread_mutex_t *mutex)` | Try to lock mutex (non-blocking) |
| **pthread_mutex_timedlock** | `int pthread_mutex_timedlock(pthread_mutex_t *mutex, const struct timespec *abs_timeout)` | Lock mutex with timeout |
| **pthread_mutex_unlock** | `int pthread_mutex_unlock(pthread_mutex_t *mutex)` | Unlock mutex |

### Mutex Attributes

| Function | Syntax | Description |
|----------|--------|-------------|
| **pthread_mutexattr_init** | `int pthread_mutexattr_init(pthread_mutexattr_t *attr)` | Initialize mutex attributes |
| **pthread_mutexattr_destroy** | `int pthread_mutexattr_destroy(pthread_mutexattr_t *attr)` | Destroy mutex attributes |
| **pthread_mutexattr_settype** | `int pthread_mutexattr_settype(pthread_mutexattr_t *attr, int type)` | Set mutex type |
| **pthread_mutexattr_gettype** | `int pthread_mutexattr_gettype(const pthread_mutexattr_t *attr, int *type)` | Get mutex type |

## POSIX Threads

| Function | Syntax | Description |
|----------|--------|-------------|
| **pthread_create** | `int pthread_create(pthread_t *thread, const pthread_attr_t *attr, void *(*start_routine)(void*), void *arg)` | Create new thread |
| **pthread_join** | `int pthread_join(pthread_t thread, void **retval)` | Wait for thread termination |
| **pthread_detach** | `int pthread_detach(pthread_t thread)` | Detach thread |
| **pthread_exit** | `void pthread_exit(void *retval)` | Terminate calling thread |
| **pthread_self** | `pthread_t pthread_self(void)` | Get calling thread ID |
| **pthread_equal** | `int pthread_equal(pthread_t t1, pthread_t t2)` | Compare thread IDs |
| **pthread_cancel** | `int pthread_cancel(pthread_t thread)` | Cancel thread |

### Thread Attributes

| Function | Syntax | Description |
|----------|--------|-------------|
| **pthread_attr_init** | `int pthread_attr_init(pthread_attr_t *attr)` | Initialize thread attributes |
| **pthread_attr_destroy** | `int pthread_attr_destroy(pthread_attr_t *attr)` | Destroy thread attributes |
| **pthread_attr_setdetachstate** | `int pthread_attr_setdetachstate(pthread_attr_t *attr, int detachstate)` | Set detach state |
| **pthread_attr_getdetachstate** | `int pthread_attr_getdetachstate(const pthread_attr_t *attr, int *detachstate)` | Get detach state |
| **pthread_attr_setstacksize** | `int pthread_attr_setstacksize(pthread_attr_t *attr, size_t stacksize)` | Set stack size |
| **pthread_attr_getstacksize** | `int pthread_attr_getstacksize(const pthread_attr_t *attr, size_t *stacksize)` | Get stack size |

## Condition Variables

| Function | Syntax | Description |
|----------|--------|-------------|
| **pthread_cond_init** | `int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr)` | Initialize condition variable |
| **pthread_cond_destroy** | `int pthread_cond_destroy(pthread_cond_t *cond)` | Destroy condition variable |
| **pthread_cond_wait** | `int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mutex)` | Wait on condition |
| **pthread_cond_timedwait** | `int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, const struct timespec *abstime)` | Wait on condition with timeout |
| **pthread_cond_signal** | `int pthread_cond_signal(pthread_cond_t *cond)` | Signal one waiting thread |
| **pthread_cond_broadcast** | `int pthread_cond_broadcast(pthread_cond_t *cond)` | Signal all waiting threads |

## System V Semaphores (Legacy)

| Function | Syntax | Description |
|----------|--------|-------------|
| **semget** | `int semget(key_t key, int nsems, int semflg)` | Get semaphore set |
| **semop** | `int semop(int semid, struct sembuf *sops, size_t nsops)` | Perform semaphore operations |
| **semtimedop** | `int semtimedop(int semid, struct sembuf *sops, size_t nsops, const struct timespec *timeout)` | Perform operations with timeout |
| **semctl** | `int semctl(int semid, int semnum, int cmd, ...)` | Control semaphore set |

## Low-Level Synchronization (Linux-specific)

| Function | Syntax | Description |
|----------|--------|-------------|
| **futex** | `long syscall(SYS_futex, uint32_t *uaddr, int futex_op, uint32_t val, ...)` | Fast userspace mutex |
| **clone** | `int clone(int (*fn)(void *), void *stack, int flags, void *arg, ...)` | Create process/thread |

## Common Return Values

- **Success**: Most functions return `0` on success
- **Error**: Most functions return `-1` or error code and set `errno`
- **Exceptions**: 
  - `pthread_create`, `pthread_join` return error code directly
  - `sem_open` returns `SEM_FAILED` on error
  - `pthread_self` always succeeds

## Required Headers

```c
#include <semaphore.h>     // POSIX semaphores
#include <pthread.h>       // POSIX threads and mutexes
#include <sys/sem.h>       // System V semaphores
#include <linux/futex.h>   // Futex (Linux-specific)
#include <sys/syscall.h>   // System calls
#include <unistd.h>        // Standard system calls
```

## Initialization Examples

```c
// Semaphore initialization
sem_t sem;
sem_init(&sem, 0, 1);  // pshared=0 (process-local), initial value=1

// Mutex initialization
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
// or
pthread_mutex_t mutex;
pthread_mutex_init(&mutex, NULL);

// Thread creation
pthread_t thread;
pthread_create(&thread, NULL, thread_function, arg);
```
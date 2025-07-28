# Shared Objects and Build Process: A Comprehensive Tutorial

## Table of Contents
1. [Introduction](#introduction)
2. [Build Process Fundamentals](#build-process-fundamentals)
3. [Static vs Dynamic Linking](#static-vs-dynamic-linking)
4. [Shared Objects Deep Dive](#shared-objects-deep-dive)
5. [Dynamic Linking Process](#dynamic-linking-process)
6. [Practical Examples](#practical-examples)
7. [Advanced Topics](#advanced-topics)
8. [Troubleshooting](#troubleshooting)

## Introduction

Shared objects (shared libraries) and the build process are fundamental concepts in systems programming. Understanding how code transforms from source files to executable programs, and how libraries can be shared across multiple programs, is essential for efficient software development.

**Key Benefits of Shared Libraries:**
- **Memory efficiency**: Multiple programs share a single copy in memory
- **Disk space savings**: No code duplication across executables
- **Easy updates**: Update library once, all programs benefit
- **Modularity**: Clean separation of functionality

## Build Process Fundamentals

The compilation process consists of several distinct stages orchestrated by a **compiler driver** (like `gcc`):

### 1. Preprocessing
```bash
# Preprocessing only (creates .i file)
gcc -E source.c -o source.i
```
- Expands `#include` directives
- Processes `#define` macros
- Handles conditional compilation (`#ifdef`, etc.)

### 2. Compilation
```bash
# Compile to assembly (creates .s file)
gcc -S source.c -o source.s
```
- Translates C code to assembly language
- Performs optimizations
- Generates target-specific assembly

### 3. Assembly
```bash
# Assemble to object file (creates .o file)
gcc -c source.c -o source.o
```
- Converts assembly to machine code
- Creates relocatable object file
- Includes symbol table and relocation information

### 4. Linking
```bash
# Link to create executable
gcc source.o -o program
```
- Combines object files
- Resolves external references
- Creates final executable

## Static vs Dynamic Linking

### Static Linking
```bash
# Static linking (includes library code in executable)
gcc -static program.c -lmath -o program_static
```

**Characteristics:**
- Larger executable size
- No external dependencies at runtime
- Faster program startup
- Library code embedded in executable

### Dynamic Linking
```bash
# Dynamic linking (default behavior)
gcc program.c -lmath -o program_dynamic
```

**Characteristics:**
- Smaller executable size
- Requires shared libraries at runtime
- Slower startup (loading/linking overhead)
- Shared library updates affect all programs

## Shared Objects Deep Dive

### Creating a Shared Library

**Step 1: Create library source**
```c
// mathlib.c
#include <math.h>

double square(double x) {
    return x * x;
}

double cube(double x) {
    return x * x * x;
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

**Step 2: Create header file**
```c
// mathlib.h
#ifndef MATHLIB_H
#define MATHLIB_H

double square(double x);
double cube(double x);
int factorial(int n);

#endif
```

**Step 3: Compile to position-independent code**
```bash
# Create position-independent object file
gcc -fPIC -c mathlib.c -o mathlib.o
```

**Step 4: Create shared library**
```bash
# Create shared library (.so file)
gcc -shared -o libmathlib.so mathlib.o
```

### Using the Shared Library

**Method 1: Link-time binding**
```c
// main.c
#include <stdio.h>
#include "mathlib.h"

int main() {
    double x = 5.0;
    printf("Square of %.1f = %.1f\n", x, square(x));
    printf("Cube of %.1f = %.1f\n", x, cube(x));
    printf("Factorial of 5 = %d\n", factorial(5));
    return 0;
}
```

```bash
# Compile and link
gcc -o main main.c -L. -lmathlib

# Run (library must be in library path)
export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH
./main
```

**Method 2: Runtime binding with dlopen**
```c
// dynamic_main.c
#include <stdio.h>
#include <dlfcn.h>
#include <stdlib.h>

int main() {
    void *handle;
    double (*square_func)(double);
    int (*factorial_func)(int);
    char *error;
    
    // Load shared library
    handle = dlopen("./libmathlib.so", RTLD_LAZY);
    if (!handle) {
        fprintf(stderr, "dlopen error: %s\n", dlerror());
        return EXIT_FAILURE;
    }
    
    // Clear any existing error
    dlerror();
    
    // Get function addresses
    square_func = dlsym(handle, "square");
    error = dlerror();
    if (error != NULL) {
        fprintf(stderr, "dlsym error: %s\n", error);
        dlclose(handle);
        return EXIT_FAILURE;
    }
    
    factorial_func = dlsym(handle, "factorial");
    error = dlerror();
    if (error != NULL) {
        fprintf(stderr, "dlsym error: %s\n", error);
        dlclose(handle);
        return EXIT_FAILURE;
    }
    
    // Use the functions
    double x = 7.0;
    printf("Dynamic square of %.1f = %.1f\n", x, square_func(x));
    printf("Dynamic factorial of 6 = %d\n", factorial_func(6));
    
    // Close library handle
    dlclose(handle);
    return 0;
}
```

```bash
# Compile with dl library
gcc -o dynamic_main dynamic_main.c -ldl
./dynamic_main
```

## Dynamic Linking Process

### ELF File Format Structure

The **Executable and Linkable Format (ELF)** is the standard format for executables and shared libraries on Unix-like systems:

```c
// Examining ELF header
#include <stdio.h>
#include <sys/types.h>
#include <elf.h>
#include <fcntl.h>
#include <unistd.h>

void examine_elf(const char *filename) {
    int fd = open(filename, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return;
    }
    
    Elf64_Ehdr header;
    if (read(fd, &header, sizeof(header)) != sizeof(header)) {
        perror("read");
        close(fd);
        return;
    }
    
    printf("ELF Magic: %c%c%c%c\n", 
           header.e_ident[0], header.e_ident[1], 
           header.e_ident[2], header.e_ident[3]);
    printf("Class: %s\n", 
           header.e_ident[EI_CLASS] == ELFCLASS64 ? "64-bit" : "32-bit");
    printf("Data: %s\n", 
           header.e_ident[EI_DATA] == ELFDATA2LSB ? "Little-endian" : "Big-endian");
    printf("Entry Point: 0x%lx\n", header.e_entry);
    
    close(fd);
}
```

### Symbol Resolution and Relocation

**Symbol Resolution Process:**
1. **Compile time**: Compiler creates symbol references
2. **Link time**: Linker resolves static symbols
3. **Load time**: Dynamic linker resolves shared library symbols
4. **Runtime**: Late binding through PLT/GOT

**Relocation Types:**
- **R_X86_64_PC32**: PC-relative 32-bit relocation
- **R_X86_64_PLT32**: PLT-relative relocation
- **R_X86_64_GLOB_DAT**: Global data relocation

## Advanced Topics

### Position Independent Code (PIC)

PIC enables shared libraries to be loaded at any memory address:

```c
// Without PIC - absolute addressing
static int global_var = 42;
int get_global() {
    return global_var;  // Direct memory reference
}

// With PIC - relative addressing through GOT
extern int global_var;
int get_global() {
    return global_var;  // Indirect through Global Offset Table
}
```

### Procedure Linkage Table (PLT) and Global Offset Table (GOT)

- **PLT**: Contains jump instructions to library functions
- **GOT**: Contains actual addresses of functions/variables
- **Lazy binding**: Functions resolved on first call

```bash
# Examine PLT and GOT
objdump -d -j .plt program
objdump -d -j .got program
readelf -r program
```

### Library Versioning

```bash
# Create versioned library
gcc -shared -Wl,-soname,libmathlib.so.1 -o libmathlib.so.1.0.0 mathlib.o

# Create symbolic links
ln -sf libmathlib.so.1.0.0 libmathlib.so.1
ln -sf libmathlib.so.1 libmathlib.so
```

### Performance Considerations

**Optimization Strategies:**
1. **Minimize exported symbols**: Use `static` keyword
2. **Symbol visibility**: Use `__attribute__((visibility("hidden")))`
3. **Link-time optimization**: `-flto` flag
4. **Prelink**: Reduce startup time

```c
// Symbol visibility example
__attribute__((visibility("default"))) 
int public_function(int x);

__attribute__((visibility("hidden"))) 
int internal_function(int x);
```

## Troubleshooting

### Common Issues and Solutions

**1. Library not found at runtime**
```bash
# Check library dependencies
ldd program

# Set library path
export LD_LIBRARY_PATH=/path/to/lib:$LD_LIBRARY_PATH

# Or install library system-wide
sudo cp libmathlib.so /usr/local/lib
sudo ldconfig
```

**2. Symbol conflicts**
```bash
# Check symbol table
nm -D libmathlib.so
objdump -T libmathlib.so

# Use symbol versioning to resolve conflicts
```

**3. ABI compatibility issues**
```bash
# Check library compatibility
file libmathlib.so
readelf -h libmathlib.so
```

### Debugging Tools

```bash
# Trace library calls
strace -e trace=openat ./program

# Debug dynamic linking
LD_DEBUG=libs ./program
LD_DEBUG=symbols ./program
LD_DEBUG=bindings ./program

# Memory mapping
cat /proc/$(pidof program)/maps
```

## Best Practices

1. **Design for modularity**: Clear interfaces, minimal dependencies
2. **Version management**: Use semantic versioning for libraries
3. **Error handling**: Always check return values from dl* functions
4. **Memory management**: Proper cleanup with dlclose()
5. **Security**: Validate library paths, use RPATH carefully
6. **Testing**: Test with different library versions
7. **Documentation**: Maintain clear API documentation

## Summary

Shared objects and the build process are interconnected concepts that enable:
- **Efficient resource utilization** through code sharing
- **Modular software design** with clear separation of concerns  
- **Flexible deployment** with runtime library selection
- **Easy maintenance** through centralized library updates

Understanding these concepts is crucial for developing robust, maintainable systems that efficiently utilize system resources while providing the flexibility needed for complex software architectures.

---

*This tutorial combines insights from Computer Systems: A Programmer's Perspective and Linkers and Loaders to provide a comprehensive understanding of shared objects and the build process.*
# Comprehensive C++ Knowledge - Organized by Topics

## Table of Contents
1. [Language Fundamentals](#language-fundamentals)
2. [Function Overloading & Templates](#function-overloading--templates)
3. [Memory Management & Object Lifetime](#memory-management--object-lifetime)
4. [Linking, Compilation & Libraries](#linking-compilation--libraries)
5. [Object-Oriented Programming Concepts](#object-oriented-programming-concepts)
6. [Advanced Language Features](#advanced-language-features)
7. [Compiler Behavior & Optimizations](#compiler-behavior--optimizations)
8. [Best Practices & Design Principles](#best-practices--design-principles)

---

## Language Fundamentals

### References vs Pointers
- **Reference** = Alias for another variable, behaves exactly like the variable it refers to
- Under the hood: Often implemented as a pointer that is automatically dereferenced
- **Cannot be NULL directly**, but can achieve undefined behavior: `int *ip = NULL; int& ir = *ip;`

#### When to Use What:
| Use Case | Pointer (`*`) | Reference (`&`) | Recommendation |
|----------|---------------|-----------------|----------------|
| Output Parameter | `void func(int* out)` | `void func(int& out)` | **Reference** - cleaner, safer |
| Read-only Access | `void func(const T* in)` | `void func(const T& in)` | **Const Reference** - avoids copies |
| Dynamic Allocation | `T* p = new T;` | Not possible | **Pointer** required |
| Self-Referencing | `Node* next;` | Not possible | **Pointer** for linked lists |
| Array Iteration | `for(int* p=arr; ...)` | Not possible | **Pointer** for arithmetic |
| Re-seating | `p = &another_var;` | Not possible | **Pointer** to change targets |

### Const References
- **Non-const reference (`T&`)**: Can only bind to L-values (variables with addresses)
- **Const reference (`const T&`)**: Can bind to both L-values and R-values (temporaries)
- **Temporary Lifetime Extension**: Const reference bound to temporary extends its lifetime

### Namespaces
- Abstract container providing scope for identifiers
- Names within namespace must be unique
- `using` directive effect is limited to the block where declared
- **Specificity**: `using std::cout;` is "closer" match than `using namespace std;`
- **Enums** inside namespace must use namespace prefix
- **`#define` macros** are NOT affected by namespaces (processed before compilation)

---

## Function Overloading & Templates

### Function Overloading Resolution Order
1. **Perfect Fit**: Argument types exactly match parameter types
2. **Promotion**: Safe, trivial conversions
   - Non-const to const parameter
   - Non-volatile to volatile parameter
   - `char`/`short` to `int`
   - `float` to `double`
3. **Implicit Conversion**: Standard conversions (e.g., `int` to `double`)

**Multiple Parameters**: Compiler evaluates best match for each argument, selects function with lowest overall conversion cost.

### Templates

#### Why Templates Are in Headers
- Compiler needs full template definition to generate code for each specific type
- Creates new instance for each type combination used

#### Template Arguments
- **Template arguments**: Inside `< >` (e.g., `<class T>`)
- **Function arguments**: Inside `( )` (e.g., `(T arg1, T arg2)`)
- **Default parameters**: `template <class T = char>`

#### Template Argument Deduction
- Compiler deduces template arguments from function arguments
- All arguments used for deduction must have same type
- **Example failure**: `Foo(int, float)` - cannot deduce single type `T`

#### Explicit Instantiation vs Specialization
- **Explicit Instantiation**: Force creation of specific version, allows implicit conversions
  ```cpp
  Foo<int>(i, f); // Creates Foo(int, int), converts float to int
  ```
- **Specialization**: Completely different implementation for specific type
  ```cpp
  template<> void Foo<int>(int i1, int i2) { /* specialized */ }
  ```

#### Overload Resolution with Templates
1. **Perfect Match (Non-template)**: Regular function perfect match
2. **Perfect Match (Template)**: Template instantiation perfect match  
3. **Almost Perfect Match**: Non-template with implicit conversion

---

## Memory Management & Object Lifetime

### Object Composition Philosophy
- Almost all objects exist as part of other objects
- Affects dynamic allocation behavior design decisions
- For large codebases (2000+ lines), sometimes C is more appropriate

### Constructor Design Questions
**Ask these two questions for every new type:**
1. Does it make sense to initialize one object using another? (Copy constructor)
2. Does it make sense to do assignment of this object type to another? (Assignment operator)

### Shallow Pointer Copy Problem
- Must be considered every time you declare a new type
- Critical for memory management and object lifetime
- Related to the two design questions above

### Constructor Helper Functions
- **Problem**: Helper functions might work on objects not yet in stable state
- **Solution**: Declare helper functions as `static`
- **Reason**: Static functions don't receive `this` pointer, avoiding unstable object access

---

## Linking, Compilation & Libraries

### C/C++ Interoperability
- **Name Mangling**: C++ changes function names to support overloading
- **`extern "C"`**: Prevents name mangling for C compatibility
  ```cpp
  extern "C" {
      void fooV(void);
  }
  ```

#### C/C++ Compatible Headers
```c
#ifdef __cplusplus
extern "C" {
#endif

/* C-compatible declarations */
void FooV(void);

#ifdef __cplusplus
}
#endif
```

### Shared Objects (Dynamic Libraries)
- **Same Endianness Required**: Target and host must share endianness
- **Compiler Compatibility**: Must use same compiler for implicit linking
- **Using `extern "C"`**: Links C++ with C or different C++ compilers

#### Struct Compatibility Issues
- **Padding**: Different compilers may add different padding (controlled by `#pragma`)
- **Conditional Compilation**: Debug vs release builds may have different layouts
- **Bit Fields**: Highly platform-dependent and unportable

> **80% of bugs are in build/configuration, not code itself**

### Dynamic Loading Example
```c
// explicitfoofoo.h
#define FUNCNAME FooFoo
#define FUNCSTRING "FooFoo"
#define FUNCTYPE FUNCNAME##_ty
typedef int (*FUNCTYPE)(void);

// main.c
void *h1 = dlopen("./foofoo7.so", RTLD_LAZY);
FUNCTYPE f1 = (FUNCTYPE)dlsym(h1, FUNCSTRING);
int result = (*f1)();
```

---

## Object-Oriented Programming Concepts

### Core Terminology
- **Object** = Instance of a struct/class
- **Message** = Member function
- **Sending a message** = Calling/using those functions
- **Method** = Another name for public member function (meant for consumers)
- **Interface** = Symbolic name for cluster of messaging where each object receives different messages

### Interface Concept in C++
- No true "interface" in abstract OOP sense
- Can create similar constructs with various hacks
- Class's cluster of functions can be considered its interface
- **Why C++ is called "class-oriented"** rather than "object-oriented"

### Const Objects
- Const object guarantees you won't call methods that change its state
- Provides compile-time safety for state immutability

---

## Advanced Language Features

### The `inline` Keyword
- **Primary Purpose**: Tells linker it's okay for function to be defined in multiple compilation units
- **Secondary Purpose**: Hint for inline expansion (compiler may ignore)

#### Problems `inline` Solves
- **Multiple Definition Error**: When header function included in multiple files
- **Static Hack Downsides**: Code bloat and unused function warnings

#### How `inline` Works
- Uses weak symbols to resolve multiple definitions into single one
- Compiler can discard unused `inline` functions
- Allows function bodies in headers without linker errors

#### Costs and Dangers
1. **Code Bloat**: Large inlined functions increase executable size
2. **Increased Dependencies**: Changes require recompiling all includers
3. **False Optimization**: May not actually inline but still pay dependency cost

> "Premature optimization is the root of all evil" - Use judiciously

### Constants
- **`constexpr`**: Value can be evaluated at compile time
- **`const` Optimization**: If initialized with `constexpr`, compiler may treat as literal

### Name Mangling for Variables
- **Global Variables**: Not name-mangled (accessible across compilation units)
- **`static` and `const` Globals**: Name-mangled (internal linkage prevents conflicts)

---

## Compiler Behavior & Optimizations

### Constructor Optimization
- Even without optimization flags, compilers often inline copy constructors/assignment operators
- You may not see these functions called explicitly
- **Don't worry if constructors aren't visible** - this is compiler-dependent behavior
- Example: Class with simple `int` members may have inlined copy constructor

### Template Instantiation
- Compiler creates new instance for each type combination
- Must have full definition available at instantiation point
- This is why templates typically live in headers

---

## Best Practices & Design Principles

### Encapsulation True Meaning
- **NOT** about shrinking range of changes
- **IS** about defining and controlling range of effects in code
- **Goal**: Predictability of scope affected when changing something
- Makes code maintenance and debugging manageable

### Interface Design Practice
- Create header-only interface definitions
- No function implementations in interface
- No struct fields in interface
- Focus on designing public contract of class
- Based on "Simple String Interface" exercise requirements

### General Wisdom
- Consider C vs C++ based on project size and team
- Always follow security best practices
- Never introduce code that exposes secrets/keys
- Test thoroughly with appropriate frameworks
- Run lint and typecheck commands after significant changes

---

## CPP Intro Session 2025-08-20 with Evald

### Constructor & Destructor Philosophy

#### Default Constructor Generation Rules
- C++ promises that for every type X it's possible to call its constructor
- Constructor is generated when a member has a constructor
- **Rationale**: Don't create default ctor when parameterized constructor exists
- **Assumption**: Developer intentionally wants explicit parameter initialization

```cpp
X {
    X::X(); // ctor
    int m_i;
}

Y {
    X m_x;  // Y's constructor generated because X has constructor
    int m_i;
}
```

#### When Ctors/Dtor/Assignment Operator Won't Be Generated
1. When they are not needed (plain old structs)
2. If developer declared these functions (looked up during linking)
3. When compiler cannot (e.g. default ctor when member is const)
4. When developer created any ctor - default ctor won't be generated

### Operator Overloading Guidelines

#### Operators Provided by Default
- `operator&` (address of) - rarely used, might be confusing
- `new` and `delete` (and separately `new[]`, `delete[]`) - control memory allocation
  - Good usage: frequent allocations of same type
  - Use FSA (Fixed Size Allocation) instead of malloc for performance

#### Copy Constructor & Assignment Operator Decision Matrix
Ask these questions for every new type:
1. **Are they necessary?**
2. **If yes, are the generated ones enough?**
3. **If no to (1), declare private without implementation!**

```cpp
class X {
public:
    // Modern C++ style
    X(const X&) = delete;     // prevent generation + documentation
    X(const X&) = default;    // use default generated function
    
private:
    // Classic style
    X(const X&);             // Disabled DO NOT IMPLEMENT
    X& operator=(const X&);  // Disabled DO NOT IMPLEMENT
};
```

#### Legacy/Modern C++ Support Macros
```cpp
#if __cplusplus < 201104
#define DELETE_GENERATED(X)
#define DEFAULT_GENERATED(X)
#else 
#define DELETE_GENERATED(X)   X = delete
#define DEFAULT_GENERATED(X)  X = default
#endif

#define CLASSIC_ONLY(x) \
    do { x } while(0)
```

### The `this` Pointer

#### Characteristics
- Type: "non-lvalue pointer to X" (seen as `X* const this` in GDB - const is misleading)
- Cannot be changed by any means
- **Evald's Style Rule**: Use `this->` to call member functions/variables
- **Infinity Coding Style**:
  - `m_x` for member variables
  - `g_x` for global variables  
  - `a_` for parameters
  - Regular names for local variables

#### Usage Patterns
1. Return `*this` as reference (e.g., in assignment operator `T& operator=(const T&)`)
2. Pass address for registration: `iofactor.notify(this);`

### Access Modifiers & Encapsulation

#### Purpose of Access Modifiers
- Provide compiler-level encapsulation
- Generate compiler errors on violations
- Limit scope of changes: if member is private, type change affects only member functions

#### `const` Usage Philosophy
**Goal**: Balance between useful objects and safety - not too much const, not free access

**Thinking Habit**: For every field, ask "Will it be changed in the future?"
- If not, put const on it
- Don't put const on everything by default

**With Pointers, Ask**:
- Does the pointer need to be const?
- Does what this pointer points to need to be const?
- Continue for multiple layers of pointers

### When to Use `struct` vs `class` in C++
Use `struct` when you want to perform aggregation of data to pass or return it.

### Template Specialization

#### Use Cases
- No matching implementation in template for desired type
- Sometimes only specialization exists, generic solution unused
- Still use template signature in forward declarations

```cpp
// algo.h
template<class T>
T Calculate(T obj_, size_t i);

template<class T>
void RunAlgo(T objs_[], size_t s_) {
    size_t i = 0;
    //...
    objs_[i] = Calculate<T>(objs_[i], i);
    //...
}

// user.cpp
#include "algo.h"

template<>
X Calculate<X>(X obj_, size_t i) {
    // specialized implementation
}

int main() {
    X xs[SIZE_XS];
    RunAlgo(xs, SIZE_XS);
}
```

#### Advantages over Function Pointers
1. **No Indirection**: Avoids pointer copying and dereferencing overhead
2. **Compiler Optimizations**: Allows inlining (qsort in C slower than sort in C++)
3. **Not Possible in C**: Generated functions are definitive C++ advantage

### Static Members & Template Abuse

#### Static Member Functions
- Part of class namespace
- Affected by private/public access
- **Does NOT receive `this` pointer**

#### Abusing Templates for Static Variables
Not standard, but possible to generate static variable per type:

```cpp
template<class T>
int& Foo() {
    static int a;  // Weak symbol
    return a;
}

void Bar() {
    Foo<int>() = 5;  // l-value assignment
    Foo<X>() = 3;
}
```

### Code Review Notes from Simple String (2025-08-25)

#### Assignment Operator Best Practices
- Always handle self-assignment in operator=()
- Don't use `if(&x == this)` - handle properly without runtime check
- Write pseudo code approach in interviews

#### Constructor Helper Functions
- Be cautious about helpers called from constructors
- Dealing with uninitialized objects
- **Make them static when used this way**

### C vs C++ Usage Guidelines

#### C++ Advantages
- Maintenance - easier to maintain
- Needs setup (ctors/dtors/operator overloading/namespaces/classes)

#### C Advantages  
- Small projects (up to 2000 lines) - faster to build
- Less setup overhead

#### Const Benefits
- `const` local, private, public variables only at compiler level
- Easily bypassed but **FREE** - no runtime cost
- Helpful for finding bugs in non-const places
- **Why Evald likes them**: Zero runtime overhead safety

### OOP Theory vs C++ Implementation

| OOP Concept | C++ Implementation | Notes |
|-------------|-------------------|-------|
| Object | Struct/Class | Basic component accepting messages |
| Message | Member Function | Sending message = invoking function |
| State | Member field values | Current object data |
| Interface | Doesn't really exist | Can simulate, unlike Java's interface |

**Note**: API doesn't include constructors from OOP perspective - just "setup".
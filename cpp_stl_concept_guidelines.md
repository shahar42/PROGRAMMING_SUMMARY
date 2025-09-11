# C++ STL Container Concept Extraction Guidelines

## What is a "Concept" for C++ STL Containers?

### Definition
An **atomic STL concept** is a single, focused programming principle that teaches one specific aspect of C++ Standard Library containers, iterators, or algorithms.

### Concept Length & Scope
- **ONE concept per extraction** - focus on the most prominent container/algorithm feature
- **2-4 sentences explanation** - clear but not verbose
- **Complete, compilable C++ program** - 10-25 lines typical
- **Modern C++ style** - prefer C++11/14/17 features when appropriate

## Concept Categories for STL

### Container Categories
- `stl_seq_` - Sequential containers (vector, deque, list, array)
- `stl_assoc_` - Associative containers (set, map, multiset, multimap)
- `stl_unord_` - Unordered containers (unordered_set, unordered_map, etc.)
- `stl_adapt_` - Container adapters (stack, queue, priority_queue)

### Algorithm Categories
- `stl_algo_` - Algorithms (sort, find, transform, etc.)
- `stl_iter_` - Iterators (begin/end, iterator types, iterator arithmetic)
- `stl_func_` - Function objects and lambdas with STL

### Utility Categories
- `stl_util_` - Utility functions (make_pair, swap, move, etc.)
- `stl_smart_` - Smart pointers (unique_ptr, shared_ptr, weak_ptr)

## Naming Convention
Format: `cpp_stl_{category}_{normalized_concept_name}_{hash}.json`

Examples:
- `cpp_stl_seq_vector_push_back_a3f2d1.json`
- `cpp_stl_algo_sort_comparator_b8c4e2.json`
- `cpp_stl_iter_range_based_for_d5f6a3.json`

## What Makes a Good STL Concept?

### ✅ GOOD Examples:
- **"std::vector push_back operation"** - specific operation on specific container
- **"Range-based for loop with containers"** - specific iteration technique
- **"std::sort with custom comparator"** - specific algorithm with customization
- **"std::unique_ptr RAII pattern"** - specific smart pointer usage

### ❌ AVOID These:
- **"C++ containers overview"** - too broad, multiple concepts
- **"Variables and data types"** - basic C++, not STL-specific
- **"Inheritance and polymorphism"** - OOP concepts, not container-focused
- **"Template metaprogramming"** - too advanced, not practical STL usage

## Required JSON Structure

```json
{
  "topic": "std::vector push_back Operation",
  "explanation": "The push_back() method adds an element to the end of a std::vector, automatically managing memory reallocation when needed. This is the most common way to dynamically grow a vector during runtime.",
  "syntax": "vector.push_back(element);",
  "code_example": [
    "#include <iostream>",
    "#include <vector>",
    "",
    "int main() {",
    "    std::vector<int> numbers;",
    "    numbers.push_back(10);",
    "    numbers.push_back(20);",
    "    numbers.push_back(30);",
    "    ",
    "    for (const auto& num : numbers) {",
    "        std::cout << num << \" \";",
    "    }",
    "    return 0;",
    "}"
  ],
  "example_explanation": "This program creates an empty vector and uses push_back() to add three integers. The range-based for loop demonstrates how to iterate through the vector after adding elements. The vector automatically manages memory allocation as elements are added."
}
```

## Quality Standards

### Explanation Requirements
- **What**: Clearly state what the concept is
- **Why**: Explain when/why you'd use it
- **Context**: How it fits in STL ecosystem
- **Length**: 2-4 sentences maximum

### Code Example Requirements
- **Complete**: Must compile and run
- **Minimal**: Only demonstrates the target concept
- **Modern**: Use `auto`, range-based loops, `std::` prefix
- **Practical**: Realistic use case, not contrived
- **Includes**: Necessary headers (`<iostream>`, `<vector>`, etc.)

### Example Explanation Requirements
- **Step-by-step**: Walk through what the code does
- **Concept link**: Explicitly connect code to the concept
- **Behavior**: Mention any important runtime behavior
- **Length**: 2-3 sentences maximum

## Focus Areas for STL Containers Book

### High Priority Concepts
1. **Container Operations**: insert, erase, push_back, emplace
2. **Iterator Usage**: begin/end, iterator arithmetic, iterator types
3. **Algorithm Application**: sort, find, transform with containers
4. **Memory Management**: RAII, smart pointers, move semantics
5. **Performance Considerations**: when to use which container

### Medium Priority
1. **Container Adapters**: stack, queue, priority_queue
2. **Associative Containers**: set/map operations and use cases
3. **Custom Comparators**: sorting and searching with custom logic
4. **Exception Safety**: strong exception guarantee with containers

### Lower Priority
1. **Advanced Template Features**: SFINAE, perfect forwarding
2. **Low-level Details**: allocator customization
3. **Legacy Features**: pre-C++11 patterns
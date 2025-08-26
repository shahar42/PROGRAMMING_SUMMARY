#include "my_string.hpp"
#include <iostream>
#include <cassert>
#include <chrono>

void test_basic_functionality() {
    std::cout << "=== Testing Basic Functionality ===\n";
    
    // Test default constructor
    MyString empty;
    assert(empty.empty());
    assert(empty.size() == 0);
    std::cout << "✓ Default constructor works\n";
    
    // Test C-string constructor (SSO)
    MyString small("Hello");
    assert(small.size() == 5);
    assert(std::string(small.c_str()) == "Hello");
    std::cout << "✓ C-string constructor (SSO) works\n";
    
    // Test C-string constructor (heap allocation)
    MyString large("This is a very long string that will definitely exceed SSO capacity");
    assert(large.size() == 67);
    assert(large.capacity() > 15);  // Should be on heap
    std::cout << "✓ C-string constructor (heap) works\n";
    
    // Test copy constructor
    MyString copy_small = small;
    assert(copy_small == small);
    assert(copy_small.c_str() != small.c_str());  // Different memory
    std::cout << "✓ Copy constructor works\n";
    
    // Test move constructor
    MyString original("Move me");
    MyString moved = std::move(original);
    assert(moved.size() == 7);
    assert(std::string(moved.c_str()) == "Move me");
    assert(original.empty());  // Original should be empty after move
    std::cout << "✓ Move constructor works\n";
}

void test_string_operations() {
    std::cout << "\n=== Testing String Operations ===\n";
    
    // Test append
    MyString str("Hello");
    str.append(" World");
    assert(std::string(str.c_str()) == "Hello World");
    std::cout << "✓ Append works\n";
    
    // Test += operator
    MyString str2("C++");
    str2 += " is";
    str2 += " awesome!";
    assert(std::string(str2.c_str()) == "C++ is awesome!");
    std::cout << "✓ += operator works\n";
    
    // Test + operator
    MyString left("Left");
    MyString right("Right");
    MyString combined = left + right;
    assert(std::string(combined.c_str()) == "LeftRight");
    std::cout << "✓ + operator works\n";
    
    // Test character access
    MyString indexed("Test");
    assert(indexed[0] == 'T');
    assert(indexed[3] == 't');
    indexed[0] = 'B';
    assert(std::string(indexed.c_str()) == "Best");
    std::cout << "✓ Character access works\n";
    
    // Test at() with bounds checking
    try {
        indexed.at(100);  // Should throw
        assert(false);    // Should not reach here
    } catch (const std::out_of_range&) {
        std::cout << "✓ Bounds checking works\n";
    }
}

void test_memory_management() {
    std::cout << "\n=== Testing Memory Management ===\n";
    
    // Test reserve
    MyString str("Small");
    str.reserve(100);
    assert(str.capacity() >= 100);
    assert(std::string(str.c_str()) == "Small");  // Content unchanged
    std::cout << "✓ Reserve works\n";
    
    // Test resize
    MyString resizable("Resize");
    resizable.resize(3);
    assert(std::string(resizable.c_str()) == "Res");
    
    resizable.resize(10, 'X');
    assert(resizable.size() == 10);
    assert(resizable[9] == 'X');
    std::cout << "✓ Resize works\n";
    
    // Test clear
    MyString clearable("Clear me");
    clearable.clear();
    assert(clearable.empty());
    assert(clearable.size() == 0);
    std::cout << "✓ Clear works\n";
}

void test_sso_optimization() {
    std::cout << "\n=== Testing SSO Optimization ===\n";
    
    // Test that small strings use SSO
    MyString small("Short");
    std::cout << "Small string capacity: " << small.capacity() << " (should be 15)\n";
    assert(small.capacity() == 15);
    
    // Test transition from SSO to heap
    MyString growing("Start");
    growing.reserve(50);  // Force transition to heap
    assert(growing.capacity() >= 50);
    assert(std::string(growing.c_str()) == "Start");
    std::cout << "✓ SSO to heap transition works\n";
    
    // Add more text to verify heap allocation
    growing += " small, then grow very large to exceed SSO capacity completely";
    assert(growing.size() > 15);
    assert(growing.capacity() > 15);
    std::cout << "✓ Heap allocation for large strings works\n";
}

void test_iterators() {
    std::cout << "\n=== Testing Iterators ===\n";
    
    MyString str("Iterator");
    
    // Test begin/end
    std::string collected;
    for (auto it = str.begin(); it != str.end(); ++it) {
        collected += *it;
    }
    assert(collected == "Iterator");
    std::cout << "✓ Iterator traversal works\n";
    
    // Test range-based for loop
    std::string collected2;
    for (char c : str) {
        collected2 += c;
    }
    assert(collected2 == "Iterator");
    std::cout << "✓ Range-based for loop works\n";
    
    // Test const iterators
    const MyString const_str("Const");
    std::string collected3;
    for (auto it = const_str.cbegin(); it != const_str.cend(); ++it) {
        collected3 += *it;
    }
    assert(collected3 == "Const");
    std::cout << "✓ Const iterators work\n";
}

void performance_comparison() {
    std::cout << "\n=== Performance Comparison ===\n";
    
    const int iterations = 100000;
    
    // Test without reserve (many reallocations)
    auto start = std::chrono::high_resolution_clock::now();
    MyString slow_string;
    for (int i = 0; i < iterations; ++i) {
        slow_string += "a";
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto slow_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    // Test with reserve (single allocation)
    start = std::chrono::high_resolution_clock::now();
    MyString fast_string;
    fast_string.reserve(iterations);  // Pre-allocate
    for (int i = 0; i < iterations; ++i) {
        fast_string += "a";
    }
    end = std::chrono::high_resolution_clock::now();
    auto fast_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "Without reserve: " << slow_time.count() << " μs\n";
    std::cout << "With reserve: " << fast_time.count() << " μs\n";
    std::cout << "Speedup: " << static_cast<double>(slow_time.count()) / fast_time.count() << "x\n";
    
    assert(slow_string.size() == fast_string.size());
    assert(slow_string == fast_string);
}

void demonstrate_usage() {
    std::cout << "\n=== Usage Examples ===\n";
    
    // Basic usage
    MyString greeting("Hello");
    MyString target("World");
    MyString message = greeting + ", " + target + "!";
    std::cout << "Message: " << message << "\n";
    
    // Building strings efficiently
    MyString poem;
    poem.reserve(200);  // Pre-allocate for efficiency
    poem += "Roses are red,\n";
    poem += "Violets are blue,\n";
    poem += "C++ strings are fast,\n";
    poem += "When implemented by you!\n";
    std::cout << "\nPoem:\n" << poem << "\n";
    
    // Character manipulation
    MyString editable("Programming");
    editable[0] = 'p';  // Make it lowercase
    std::cout << "Edited: " << editable << "\n";
    
    // Working with iterators
    MyString reversible("ABCDEF");
    std::cout << "Original: " << reversible << "\n";
    std::cout << "Reversed: ";
    for (auto it = reversible.end() - 1; it >= reversible.begin(); --it) {
        std::cout << *it;
    }
    std::cout << "\n";
}

int main() {
    try {
        test_basic_functionality();
        test_string_operations();
        test_memory_management();
        test_sso_optimization();
        test_iterators();
        performance_comparison();
        demonstrate_usage();
        
        std::cout << "\n🎉 All tests passed! MyString implementation is working correctly!\n";
        
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
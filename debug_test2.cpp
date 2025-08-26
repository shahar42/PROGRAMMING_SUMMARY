#include "my_string.hpp"
#include <iostream>
#include <cstring>

int main() {
    std::cout << "=== Debug Test 2 ===\n";
    
    // Reproduce exact failing sequence
    MyString growing("Start");
    std::cout << "1. Initial: size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    growing.reserve(50);
    std::cout << "2. After reserve(50): size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    // This is the exact string from the test
    const char* str = " small, then grow very large to exceed SSO capacity completely";
    size_t str_len = std::strlen(str);
    size_t current_size = growing.size();
    size_t new_size = current_size + str_len;
    
    std::cout << "3. About to append string of length " << str_len << "\n";
    std::cout << "   Current size: " << current_size << "\n";
    std::cout << "   New size will be: " << new_size << "\n";
    std::cout << "   Current capacity: " << growing.capacity() << "\n";
    std::cout << "   Need capacity: " << new_size + 1 << " (including null terminator)\n";
    
    if (new_size >= growing.capacity()) {
        std::cout << "4. Will call reserve(" << new_size + 1 << ")\n";
    } else {
        std::cout << "4. No need to reserve, current capacity is sufficient\n";
    }
    
    growing += str;
    
    std::cout << "5. Success! Final size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    return 0;
}
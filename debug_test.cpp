#include "my_string.hpp"
#include <iostream>

int main() {
    std::cout << "=== Debug Test ===\n";
    
    // Test the specific failing case
    MyString growing("Start");
    std::cout << "Initial: size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    // Reserve 50
    growing.reserve(50);
    std::cout << "After reserve(50): size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    // Try to add the long string
    const char* long_str = " small, then grow very large to exceed SSO capacity completely";
    size_t long_str_len = std::strlen(long_str);
    std::cout << "Adding string of length: " << long_str_len << "\n";
    std::cout << "New total size would be: " << growing.size() + long_str_len << "\n";
    
    // This should trigger the buffer overflow
    growing += long_str;
    
    std::cout << "Success! Final size=" << growing.size() << ", capacity=" << growing.capacity() << "\n";
    
    return 0;
}
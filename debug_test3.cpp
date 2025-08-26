#include "my_string.hpp"
#include <iostream>
#include <cassert>

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

int main() {
    test_sso_optimization();
    std::cout << "Test completed successfully!\n";
    return 0;
}
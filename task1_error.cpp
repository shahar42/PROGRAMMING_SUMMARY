#include <iostream>

// Task 1: Missing Template Declaration
// This will cause compilation error: "T was not declared in this scope"

T maxValue(T a, T b) {  // ERROR: Missing template declaration
    return (a > b) ? a : b;
}

int main() {
    std::cout << maxValue(5, 3) << std::endl;
    std::cout << maxValue(4.2, 3.7) << std::endl;
    
    return 0;
}
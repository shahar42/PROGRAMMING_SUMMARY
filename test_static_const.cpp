#include "test_static_const.h"
#include <iostream>

// Note: NO explicit definition of MAX_NUM here
// const int X::MAX_NUM = 7;  // Commented out - not needed!

void X::Foo()
{
    int i1 = MAX_NUM;              // Uses compile-time constant

    const int i = MAX_NUM;         // Copy initialization
    const int* ip = &MAX_NUM;      // Forces memory allocation!

    std::cout << "Value: " << *ip << std::endl;
    std::cout << "Address: " << ip << std::endl;
}

int X::s_i = 6;  // This needs explicit definition

int main() {
    X obj;
    obj.Foo();
    return 0;
}
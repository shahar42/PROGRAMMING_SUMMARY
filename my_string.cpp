#include "my_string.hpp"
#include <algorithm>
#include <cstdlib>

// Default constructor
MyString::MyString() : size_(0), is_large_(false) {
    // Initialize small buffer with empty string
    small_buffer_[0] = '\0';
}

// C-string constructor
MyString::MyString(const char* str) {
    if (!str) {
        // Handle null pointer
        size_ = 0;
        is_large_ = false;
        small_buffer_[0] = '\0';
        return;
    }
    
    size_ = std::strlen(str);
    
    if (size_ <= SSO_CAPACITY) {
        // Use SSO - copy to small buffer
        is_large_ = false;
        std::memcpy(small_buffer_, str, size_ + 1);  // +1 for null terminator
    } else {
        // Allocate on heap
        is_large_ = true;
        large_.capacity_ = size_ + 1;  // At least size + 1 for null terminator
        large_.data_ = static_cast<char*>(std::malloc(large_.capacity_));
        
        if (!large_.data_) {
            throw std::bad_alloc();
        }
        
        std::memcpy(large_.data_, str, size_ + 1);
    }
}

// Copy constructor
MyString::MyString(const MyString& other) : size_(other.size_), is_large_(other.is_large_) {
    if (other.is_small()) {
        // Copy small buffer
        std::memcpy(small_buffer_, other.small_buffer_, SSO_CAPACITY + 1);
    } else {
        // Allocate new memory and copy
        large_.capacity_ = other.large_.capacity_;
        large_.data_ = static_cast<char*>(std::malloc(large_.capacity_));
        
        if (!large_.data_) {
            throw std::bad_alloc();
        }
        
        std::memcpy(large_.data_, other.large_.data_, size_ + 1);
    }
}

// Move constructor
MyString::MyString(MyString&& other) noexcept : size_(other.size_), is_large_(other.is_large_) {
    if (other.is_small()) {
        // Copy small buffer (can't move from stack storage)
        std::memcpy(small_buffer_, other.small_buffer_, SSO_CAPACITY + 1);
    } else {
        // Steal heap-allocated memory
        large_.data_ = other.large_.data_;
        large_.capacity_ = other.large_.capacity_;
    }
    
    // Reset other to empty state regardless of size
    other.size_ = 0;
    other.is_large_ = false;
    other.small_buffer_[0] = '\0';
}

// Destructor
MyString::~MyString() {
    if (!is_small()) {
        std::free(large_.data_);
    }
    // Small buffer is automatic storage - no need to free
}

// Copy assignment operator
MyString& MyString::operator=(const MyString& other) {
    if (this == &other) {
        return *this;  // Self-assignment guard
    }
    
    // Clean up current resources if needed
    if (!is_small()) {
        std::free(large_.data_);
    }
    
    size_ = other.size_;
    is_large_ = other.is_large_;
    
    if (other.is_small()) {
        // Copy small buffer
        std::memcpy(small_buffer_, other.small_buffer_, SSO_CAPACITY + 1);
    } else {
        // Allocate new memory and copy
        large_.capacity_ = other.large_.capacity_;
        large_.data_ = static_cast<char*>(std::malloc(large_.capacity_));
        
        if (!large_.data_) {
            // Restore to valid state before throwing
            size_ = 0;
            is_large_ = false;
            small_buffer_[0] = '\0';
            throw std::bad_alloc();
        }
        
        std::memcpy(large_.data_, other.large_.data_, size_ + 1);
    }
    
    return *this;
}

// Move assignment operator
MyString& MyString::operator=(MyString&& other) noexcept {
    if (this == &other) {
        return *this;  // Self-assignment guard
    }
    
    // Clean up current resources
    if (!is_small()) {
        std::free(large_.data_);
    }
    
    size_ = other.size_;
    is_large_ = other.is_large_;
    
    if (other.is_small()) {
        // Copy small buffer
        std::memcpy(small_buffer_, other.small_buffer_, SSO_CAPACITY + 1);
    } else {
        // Steal heap-allocated memory
        large_.data_ = other.large_.data_;
        large_.capacity_ = other.large_.capacity_;
    }
    
    // Reset other to empty state
    other.size_ = 0;
    other.is_large_ = false;
    other.small_buffer_[0] = '\0';
    
    return *this;
}

// String append operations
MyString& MyString::append(const char* str) {
    if (!str) return *this;
    
    size_t str_len = std::strlen(str);
    if (str_len == 0) return *this;
    
    size_t new_size = size_ + str_len;
    
    // Check if we need to grow (need space for null terminator)
    if (new_size >= capacity()) {
        reserve(new_size + 1);
    }
    
    // Copy the string
    std::memcpy(data_ptr() + size_, str, str_len + 1);  // +1 for null terminator
    size_ = new_size;
    
    return *this;
}

MyString& MyString::append(const MyString& other) {
    return append(other.c_str());
}

MyString& MyString::operator+=(const char* str) {
    return append(str);
}

MyString& MyString::operator+=(const MyString& other) {
    return append(other);
}

MyString& MyString::operator+=(char c) {
    char temp[2] = {c, '\0'};
    return append(temp);
}

// Memory management
void MyString::reserve(size_t new_cap) {
    if (new_cap <= capacity()) {
        return;  // Already have enough capacity
    }
    
    // new_cap should already include space for null terminator if needed
    
    if (is_small() && new_cap > SSO_CAPACITY) {
        // Transition from small to large
        char* new_data = static_cast<char*>(std::malloc(new_cap));
        if (!new_data) {
            throw std::bad_alloc();
        }
        
        // Copy small buffer to heap
        std::memcpy(new_data, small_buffer_, size_ + 1);
        
        // Switch to large mode
        is_large_ = true;
        large_.data_ = new_data;
        large_.capacity_ = new_cap;
    } else if (!is_small()) {
        // Reallocate heap memory
        char* new_data = static_cast<char*>(std::realloc(large_.data_, new_cap));
        if (!new_data) {
            throw std::bad_alloc();
        }
        
        large_.data_ = new_data;
        large_.capacity_ = new_cap;
    }
    // If still small and new_cap <= SSO_CAPACITY, no action needed
}

void MyString::resize(size_t new_size, char fill) {
    if (new_size == size_) {
        return;
    }
    
    if (new_size > capacity()) {
        reserve(new_size);
    }
    
    char* data = data_ptr();
    
    if (new_size > size_) {
        // Fill with fill character
        std::fill(data + size_, data + new_size, fill);
    }
    
    size_ = new_size;
    data[size_] = '\0';  // Null terminate
}

void MyString::clear() noexcept {
    size_ = 0;
    data_ptr()[0] = '\0';
    // Don't deallocate memory - just mark as empty
}

// Comparison operators
bool MyString::operator==(const MyString& other) const noexcept {
    if (size_ != other.size_) {
        return false;
    }
    return std::memcmp(data_ptr(), other.data_ptr(), size_) == 0;
}

bool MyString::operator!=(const MyString& other) const noexcept {
    return !(*this == other);
}

bool MyString::operator<(const MyString& other) const noexcept {
    int result = std::memcmp(data_ptr(), other.data_ptr(), 
                            std::min(size_, other.size_));
    if (result != 0) {
        return result < 0;
    }
    return size_ < other.size_;
}

// Non-member operators
MyString operator+(const MyString& lhs, const MyString& rhs) {
    MyString result = lhs;
    result += rhs;
    return result;
}

MyString operator+(const MyString& lhs, const char* rhs) {
    MyString result = lhs;
    result += rhs;
    return result;
}

MyString operator+(const char* lhs, const MyString& rhs) {
    MyString result(lhs);
    result += rhs;
    return result;
}

std::ostream& operator<<(std::ostream& os, const MyString& str) {
    return os << str.c_str();
}
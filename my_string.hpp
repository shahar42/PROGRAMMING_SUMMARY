#ifndef MY_STRING_HPP
#define MY_STRING_HPP

#include <cstring>
#include <memory>
#include <stdexcept>
#include <ostream>

class MyString {
private:
    // Small String Optimization constants
    static constexpr size_t SSO_CAPACITY = 15;  // 15 chars + null terminator
    static constexpr size_t LARGE_FLAG = SIZE_MAX;  // Flag for large strings
    
    // Union for SSO implementation
    union {
        char small_buffer_[SSO_CAPACITY + 1];  // +1 for null terminator
        struct {
            char* data_;
            size_t capacity_;
        } large_;
    };
    
    size_t size_;
    bool is_large_;  // Track whether we're using heap allocation
    
    // Helper functions
    bool is_small() const noexcept { 
        return !is_large_; 
    }
    
    char* data_ptr() noexcept {
        return is_small() ? small_buffer_ : large_.data_;
    }
    
    const char* data_ptr() const noexcept {
        return is_small() ? small_buffer_ : large_.data_;
    }
    
    void set_large_data(char* ptr, size_t cap) {
        large_.data_ = ptr;
        large_.capacity_ = cap;
    }

public:
    // Forward declarations for Part 2
    MyString();
    MyString(const char* str);
    MyString(const MyString& other);
    MyString(MyString&& other) noexcept;
    ~MyString();
    
    MyString& operator=(const MyString& other);
    MyString& operator=(MyString&& other) noexcept;
    
    // Core interface methods (Part 3)
    size_t size() const noexcept { return size_; }
    size_t length() const noexcept { return size_; }
    bool empty() const noexcept { return size_ == 0; }
    
    size_t capacity() const noexcept {
        return is_small() ? SSO_CAPACITY : large_.capacity_;
    }
    
    const char* c_str() const noexcept {
        return data_ptr();
    }
    
    const char* data() const noexcept {
        return data_ptr();
    }
    
    // Character access
    char& operator[](size_t index) noexcept {
        return data_ptr()[index];
    }
    
    const char& operator[](size_t index) const noexcept {
        return data_ptr()[index];
    }
    
    char& at(size_t index) {
        if (index >= size_) {
            throw std::out_of_range("MyString::at: index out of range");
        }
        return data_ptr()[index];
    }
    
    const char& at(size_t index) const {
        if (index >= size_) {
            throw std::out_of_range("MyString::at: index out of range");
        }
        return data_ptr()[index];
    }
    
    // String operations (Part 4)
    MyString& append(const char* str);
    MyString& append(const MyString& other);
    MyString& operator+=(const char* str);
    MyString& operator+=(const MyString& other);
    MyString& operator+=(char c);
    
    // Memory management (Part 5)
    void reserve(size_t new_cap);
    void resize(size_t new_size, char fill = '\0');
    void clear() noexcept;
    
    // Comparison operators
    bool operator==(const MyString& other) const noexcept;
    bool operator!=(const MyString& other) const noexcept;
    bool operator<(const MyString& other) const noexcept;
    
    // Iterator support (Part 6)
    using iterator = char*;
    using const_iterator = const char*;
    
    iterator begin() noexcept { return data_ptr(); }
    iterator end() noexcept { return data_ptr() + size_; }
    const_iterator begin() const noexcept { return data_ptr(); }
    const_iterator end() const noexcept { return data_ptr() + size_; }
    const_iterator cbegin() const noexcept { return data_ptr(); }
    const_iterator cend() const noexcept { return data_ptr() + size_; }
};

// Non-member operators
MyString operator+(const MyString& lhs, const MyString& rhs);
MyString operator+(const MyString& lhs, const char* rhs);
MyString operator+(const char* lhs, const MyString& rhs);

std::ostream& operator<<(std::ostream& os, const MyString& str);

#endif // MY_STRING_HPP
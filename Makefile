CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -g
TARGET = test_string
SOURCES = my_string.cpp test_my_string.cpp

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCES)

test: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

debug: CXXFLAGS += -DDEBUG -fsanitize=address -fsanitize=undefined
debug: $(TARGET)

valgrind: $(TARGET)
	valgrind --leak-check=full --show-leak-kinds=all ./$(TARGET)

help:
	@echo "Available targets:"
	@echo "  all     - Build the test program"
	@echo "  test    - Build and run tests"
	@echo "  debug   - Build with debug flags and sanitizers"
	@echo "  valgrind - Run with memory leak detection"
	@echo "  clean   - Remove built files"
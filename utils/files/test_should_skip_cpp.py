from utils.files.should_skip_cpp import should_skip_cpp


def test_headers_only():
    # Header file with includes and declarations only
    content = """#ifndef EXAMPLE_H
#define EXAMPLE_H

#include <iostream>
#include <vector>
#include "custom.h"

// Forward declarations
class MyClass;
struct MyStruct;

// Constants
const int MAX_SIZE = 100;
static const char* VERSION = "1.0.0";

// Function declarations
extern int calculate(int x, int y);

#endif // EXAMPLE_H"""
    assert should_skip_cpp(content) is True


def test_struct_definitions_only():
    # Struct definitions without implementation
    content = """struct Point {
    int x;
    int y;
};

struct Rectangle {
    Point topLeft;
    Point bottomRight;
};

enum Color {
    RED,
    GREEN,
    BLUE
};"""
    assert should_skip_cpp(content) is True


def test_with_function_implementation():
    # File with function implementation should not be skipped
    content = """#include <iostream>

int add(int a, int b) {
    return a + b;
}

void print_hello() {
    std::cout << "Hello World!" << std::endl;
}"""
    assert should_skip_cpp(content) is False


def test_class_with_methods():
    # Class with method implementations should not be skipped
    content = """class Calculator {
public:
    int add(int a, int b) {
        return a + b;
    }

private:
    int result;
};"""
    assert should_skip_cpp(content) is False


def test_mixed_declarations_and_definitions():
    # Mix of declarations (skip) and definitions (don't skip)
    content = """#include <vector>

// Declaration only - OK
extern int global_var;

// Function with implementation - NOT OK
int multiply(int x, int y) {
    return x * y;
}

struct Data {
    int value;
};"""
    assert should_skip_cpp(content) is False

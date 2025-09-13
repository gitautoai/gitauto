#!/usr/bin/env python3

from utils.files.should_skip_cpp import should_skip_cpp

def test_typedef_complex():
    # Complex typedef declarations
    content = """typedef int (*FunctionPtr)(int, int);
typedef struct {
    int x, y;
} Point;

typedef enum {
    RED, GREEN, BLUE
} Color;"""
    result = should_skip_cpp(content)
    print(f"Result: {result}")
    print(f"Expected: True")
    print(f"Test {'PASSED' if result is True else 'FAILED'}")

if __name__ == "__main__":
    test_typedef_complex()

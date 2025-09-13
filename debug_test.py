#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.files.should_skip_cpp import should_skip_cpp

def debug_test():
    content = """typedef int (*FunctionPtr)(int, int);
typedef struct {
    int x, y;
} Point;

typedef enum {
    RED, GREEN, BLUE
} Color;"""
    
    print("Testing content:")
    print(repr(content))
    print("\nLines:")
    for i, line in enumerate(content.split('\n')):
        print(f"{i+1}: {repr(line.strip())}")
    
    result = should_skip_cpp(content)
    print(f"\nResult: {result}")
    return result

if __name__ == "__main__":
    debug_test()
#!/usr/bin/env python3

import sys
sys.path.append('.')

from utils.files.should_skip_go import should_skip_go

# Test the nested struct case
content = """package main

type Outer struct {
    Inner struct {
        Value string
        Count int
    }
    Name string
}"""

# Test simple struct case
simple_struct = """package main

type User struct {
    ID   int64
    Name string
}"""

# Test struct with function (should return False)
struct_with_func = """package main

type User struct {
    ID   int64
    Name string
}

func (u *User) GetName() string {
    return u.Name
}"""

# Test interface case
interface_content = """package main

type Reader interface {
    Read([]byte) (int, error)
}"""

print("=== Testing nested struct ===")
result = should_skip_go(content)
print(f"should_skip_go result: {result}")
print(f"Expected: True")
print(f"Test {'PASSED' if result is True else 'FAILED'}")

print("\n=== Testing simple struct ===")
result2 = should_skip_go(simple_struct)
print(f"should_skip_go result: {result2}")
print(f"Expected: True")
print(f"Test {'PASSED' if result2 is True else 'FAILED'}")

print("\n=== Testing struct with function ===")
result3 = should_skip_go(struct_with_func)
print(f"should_skip_go result: {result3}")
print(f"Expected: False")
print(f"Test {'PASSED' if result3 is False else 'FAILED'}")

print("\n=== Testing interface ===")
result4 = should_skip_go(interface_content)
print(f"should_skip_go result: {result4}")
print(f"Expected: True")
print(f"Test {'PASSED' if result4 is True else 'FAILED'}")
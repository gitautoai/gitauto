import sys
sys.path.insert(0, '.')
from utils.files.should_skip_go import should_skip_go

# Test the exact failing case
content = """package main

type Outer struct {
    Inner struct {
        Value string
        Count int
    }
    Name string
}"""

print("Testing nested struct case:")
print("Content:")
print(repr(content))
print()

# Let's trace through the logic manually
lines = content.split("\n")
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line.strip())}")

print()
result = should_skip_go(content)
print(f"Result: {result}")
print(f"Expected: True")
print(f"Test: {'PASS' if result is True else 'FAIL'}")

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

result = should_skip_go(content)
print(f"should_skip_go result: {result}")
print(f"Expected: True")
print(f"Test {'PASSED' if result is True else 'FAILED'}")

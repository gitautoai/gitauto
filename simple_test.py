#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.files.should_skip_rust import should_skip_rust

# Test case 1: struct Config {} should return True (skip)
content1 = """struct Config {}"""
result1 = should_skip_rust(content1)
print(f"Test 1 - struct Config {{}}: {result1} (expected: True)")

# Test case 2: struct + impl should return False (don't skip)
content2 = """struct Config {}

impl Config {
    fn handler(&self) -> &str {
        "error"
    }
}"""
result2 = should_skip_rust(content2)
print(f"Test 2 - struct + impl: {result2} (expected: False)")

print(f"Tests passed: {result1 == True and result2 == False}")

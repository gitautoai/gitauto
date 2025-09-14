#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.files.should_skip_go import should_skip_go

# Test 1: Simple constants (should be True)
content1 = """package main

const MaxRetries = 3"""
result1 = should_skip_go(content1)
print(f"Test 1 (constants): {result1} (expected: True)")

# Test 2: Function (should be False)
content2 = """package main

func doSomething() {
    return
}"""
result2 = should_skip_go(content2)
print(f"Test 2 (function): {result2} (expected: False)")

# Test 3: Build tags (should be True)
content3 = """//go:build linux

package main

const MaxRetries = 3"""
result3 = should_skip_go(content3)
print(f"Test 3 (build tags): {result3} (expected: True)")

print("Validation complete!")

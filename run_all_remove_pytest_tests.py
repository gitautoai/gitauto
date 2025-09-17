#!/usr/bin/env python3
import os
import sys
import inspect

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import the test module
import utils.logs.test_remove_pytest_sections as test_module

# Get all test functions
test_functions = [
    getattr(test_module, name)
    for name in dir(test_module)
    if name.startswith('test_') and callable(getattr(test_module, name))
]

print(f"Found {len(test_functions)} test functions")

passed = 0
failed = 0

for test_func in test_functions:
    test_name = test_func.__name__
    try:
        test_func()
        print(f"✓ {test_name}")
        passed += 1
    except AssertionError as e:
        print(f"✗ {test_name}: {e}")
        failed += 1
    except Exception as e:
        print(f"✗ {test_name}: ERROR - {e}")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")

# Also test the specific case that's mentioned in the error
print("\n" + "="*50)
print("Testing specific cases:")

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test None
result = remove_pytest_sections(None)
print(f"None input: {result} (type: {type(result)}) - Expected: None")
print(f"None test passes: {result is None}")

# Test empty string
result = remove_pytest_sections("")
print(f"Empty input: {repr(result)} (type: {type(result)}) - Expected: ''")
print(f"Empty test passes: {result == ''}")

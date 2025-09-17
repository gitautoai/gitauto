#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Test the function directly
from utils.logs.remove_pytest_sections import remove_pytest_sections

print("Testing remove_pytest_sections function...")

# Test 1: None input
result = remove_pytest_sections(None)
print(f"1. None input: {result} (type: {type(result)}) - Expected: None - Pass: {result is None}")

# Test 2: Empty string
result = remove_pytest_sections("")
print(f"2. Empty input: {repr(result)} (type: {type(result)}) - Expected: '' - Pass: {result == ''}")

# Test 3: Basic functionality
log = """Run python -m pytest
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /github/workspace
plugins: cov-6.0.0
collecting ... collected 2 items

test_example.py::test_pass PASSED                                       [ 50%]
test_example.py::test_fail FAILED                                       [100%]

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError
=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

expected = """Run python -m pytest

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

result = remove_pytest_sections(log)
match = result == expected
print(f"3. Basic functionality - Pass: {match}")

if not match:
    print("\nResult:")
    result_lines = result.split('\n')
    for i, line in enumerate(result_lines):
        print(f"{i:2d}: {repr(line)}")

    print("\nExpected:")
    expected_lines = expected.split('\n')
    for i, line in enumerate(expected_lines):
        print(f"{i:2d}: {repr(line)}")

    # Find first difference
    for i, (r_line, e_line) in enumerate(zip(result_lines, expected_lines)):
        if r_line != e_line:
            print(f"\nFirst difference at line {i}:")
            print(f"Result:   {repr(r_line)}")
            print(f"Expected: {repr(e_line)}")
            break

print("\nDone.")

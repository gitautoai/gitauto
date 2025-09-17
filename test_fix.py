#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the failing case
log = """Before content
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
collecting ... collected 2 items
test_example.py::test_pass PASSED
After content"""

expected = """Before content
After content"""

result = remove_pytest_sections(log)
print(f"Result: {repr(result)}")
print(f"Expected: {repr(expected)}")
print(f"Match: {result == expected}")
print("Test passed!" if result == expected else "Test failed!")

# Test _is_pytest_line function
from utils.logs.remove_pytest_sections import _is_pytest_line
print(f"\n_is_pytest_line('After content'): {_is_pytest_line('After content')}")
print(f"_is_pytest_line('test_example.py::test_pass PASSED'): {_is_pytest_line('test_example.py::test_pass PASSED')}")
print(f"_is_pytest_line('platform linux -- Python 3.11.4'): {_is_pytest_line('platform linux -- Python 3.11.4')}")

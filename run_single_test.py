#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run a single test
from utils.logs.test_remove_pytest_sections import test_remove_pytest_sections_with_pytest_output

try:
    test_remove_pytest_sections_with_pytest_output()
    print("✓ test_remove_pytest_sections_with_pytest_output passed")
except AssertionError as e:
    print("✗ test_remove_pytest_sections_with_pytest_output failed:")
    print(f"  {e}")
except Exception as e:
    print("✗ test_remove_pytest_sections_with_pytest_output error:")
    print(f"  {e}")

# Test None input
from utils.logs.remove_pytest_sections import remove_pytest_sections
result = remove_pytest_sections(None)
print(f"None input result: {result} (type: {type(result)})")

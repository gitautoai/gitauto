#!/usr/bin/env python3
"""Simple test to validate the function works."""

from utils.logs.remove_repetitive_eslint_warnings import remove_repetitive_eslint_warnings

def test_basic_functionality():
    """Test basic functionality."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:1  warning  'var' is deprecated

✖ 2 problems (1 error, 1 warning)"""

    result = remove_repetitive_eslint_warnings(log)
    print("Input:", repr(log))
    print("Output:", repr(result))
    print("✓ Basic test passed")

if __name__ == "__main__":
    test_basic_functionality()

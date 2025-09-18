#!/usr/bin/env python3
"""Test the function directly."""

import sys
import traceback

try:
    from utils.logs.remove_repetitive_eslint_warnings import remove_repetitive_eslint_warnings

    # Test empty input
    result = remove_repetitive_eslint_warnings("")
    print(f"Empty input result: {repr(result)}")

    # Test None input
    result = remove_repetitive_eslint_warnings(None)
    print(f"None input result: {repr(result)}")

    # Test basic functionality
    log = """/path/to/file1.js
  1:1  error  Unexpected token
✖ 1 problem (1 error, 0 warnings)"""
    result = remove_repetitive_eslint_warnings(log)
    print(f"Basic test result: {repr(result)}")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()

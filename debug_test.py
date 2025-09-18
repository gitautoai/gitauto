#!/usr/bin/env python3
"""Debug test to see what's failing."""

import sys
import traceback

try:
    # Try to run just one simple test
    from utils.logs.test_remove_repetitive_eslint_warnings import test_empty_input
    test_empty_input()
    print("✓ test_empty_input passed")
except Exception as e:
    print(f"✗ Error: {e}")
    print("Traceback:")
    traceback.print_exc()

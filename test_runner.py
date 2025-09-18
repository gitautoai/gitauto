#!/usr/bin/env python3
"""Quick test runner to validate the test file."""

if __name__ == "__main__":
    try:
        from utils.logs.test_remove_repetitive_eslint_warnings import *
        print("✓ Test file imports successfully")
    except Exception as e:
        print(f"✗ Import error: {e}")

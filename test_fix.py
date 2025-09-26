#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_failing_case():
    """Test the specific failing case."""
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    print("Input:")
    print(repr(log))
    print("\nExpected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print("\nMatch:", result == expected)

    return result == expected

if __name__ == "__main__":
    success = test_failing_case()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)

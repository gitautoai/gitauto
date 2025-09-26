#!/usr/bin/env python3

import sys
sys.path.append('.')

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_failing_case():
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    print(f"Expected: {repr(expected)}")
    print(f"Got: {repr(result)}")
    print(f"Match: {result == expected}")

if __name__ == "__main__":
    test_failing_case()

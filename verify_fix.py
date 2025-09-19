#!/usr/bin/env python3
"""Verify that our fix works for the failing test cases."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_case(name, log, expected):
    """Test a single case and report results."""
    result = remove_pytest_sections(log)
    success = result == expected

    print(f"=== {name} ===")
    print(f"Success: {success}")
    if not success:
        print(f"Expected: {repr(expected)}")
        print(f"Got:      {repr(result)}")
        print("Diff:")
        expected_lines = expected.split('\n')
        result_lines = result.split('\n')
        max_lines = max(len(expected_lines), len(result_lines))
        for i in range(max_lines):
            exp_line = expected_lines[i] if i < len(expected_lines) else "<MISSING>"
            res_line = result_lines[i] if i < len(result_lines) else "<MISSING>"
            if exp_line != res_line:
                print(f"  Line {i}: Expected {repr(exp_line)}, Got {repr(res_line)}")
    print()
    return success

def main():
    """Run all test cases."""
    all_passed = True

    # Test 1: The failing test case
    log1 = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

    expected1 = """Before content
After content"""

    all_passed &= test_case("test_remove_pytest_sections_only_test_session_starts", log1, expected1)

    # Test 2: The warnings test case
    log2 = """Before content
=========================== warnings summary ============================
warning 1
warning 2
After content"""

    expected2 = """Before content
After content"""

    all_passed &= test_case("test_remove_pytest_sections_only_warnings_summary", log2, expected2)

    # Test 3: A case that should preserve blank lines
    log3 = """Content before
=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
failure content"""

    expected3 = """Content before

=================================== FAILURES ===================================
failure content"""

    all_passed &= test_case("test_remove_pytest_sections_failures_with_blank_line_handling", log3, expected3)

    print(f"Overall result: {'PASS' if all_passed else 'FAIL'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

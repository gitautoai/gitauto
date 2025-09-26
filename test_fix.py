#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_failing_case_1():
    """Test the first failing case."""
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    print("=== Test 1: test_remove_pytest_sections_only_test_session_starts ===")
    print("Input:")
    print(repr(log))
    print("\nExpected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print("\nMatch:", result == expected)

    return result == expected

def test_failing_case_2():
    """Test the second similar case."""
    log = """Initial content
=========================== warnings summary ============================
warning content
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    print("\n=== Test 2: test_remove_pytest_sections_only_warnings_summary ===")
    print("Input:")
    print(repr(log))
    print("\nExpected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print("\nMatch:", result == expected)

    return result == expected

def test_working_case():
    """Test a case that should still work."""
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
    print("\n=== Test 3: test_remove_pytest_sections_with_test_session_starts ===")
    print("Input:")
    print(repr(log))
    print("\nExpected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print("\nMatch:", result == expected)

    return result == expected

if __name__ == "__main__":
    test1 = test_failing_case_1()
    test2 = test_failing_case_2()
    test3 = test_working_case()

    all_passed = test1 and test2 and test3
    print(f"\n=== SUMMARY ===")
    print(f"Test 1: {'PASSED' if test1 else 'FAILED'}")
    print(f"Test 2: {'PASSED' if test2 else 'FAILED'}")
    print(f"Test 3: {'PASSED' if test3 else 'FAILED'}")
    print(f"Overall: {'PASSED' if all_passed else 'FAILED'}")

    sys.exit(0 if all_passed else 1)

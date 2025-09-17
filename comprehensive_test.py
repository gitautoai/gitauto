#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from utils.logs.remove_pytest_sections import remove_pytest_sections, _is_pytest_line

def test_case(name, log, expected):
    result = remove_pytest_sections(log)
    passed = result == expected
    print(f"{name}: {'✓ PASS' if passed else '✗ FAIL'}")
    if not passed:
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")
    return passed

# Test 1: The failing case
log1 = """Before content
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
collecting ... collected 2 items
test_example.py::test_pass PASSED
After content"""

expected1 = """Before content
After content"""

# Test 2: With FAILURES section
log2 = """Before content
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
collecting ... collected 2 items
=================================== FAILURES ===================================
Test failure content
After content"""

expected2 = """Before content

=================================== FAILURES ===================================
Test failure content
After content"""

# Test 3: With warnings summary
log3 = """Before content
=========================== warnings summary ============================
Warning content
After content"""

expected3 = """Before content
After content"""

# Run tests
all_passed = True
all_passed &= test_case("Test 1 (failing case)", log1, expected1)
all_passed &= test_case("Test 2 (with FAILURES)", log2, expected2)
all_passed &= test_case("Test 3 (warnings only)", log3, expected3)

# Test _is_pytest_line function
print(f"\n_is_pytest_line tests:")
print(f"  'After content': {_is_pytest_line('After content')} (should be False)")
print(f"  'test_example.py::test_pass PASSED': {_is_pytest_line('test_example.py::test_pass PASSED')} (should be True)")
print(f"  'platform linux': {_is_pytest_line('platform linux')} (should be True)")

print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
sys.exit(0 if all_passed else 1)

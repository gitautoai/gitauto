#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_warnings_summary():
    log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

/path/to/file.py:20: UserWarning: user warning
  warnings.warn("user warning")

=================================== FAILURES ===================================
Test failure content here"""

    expected = """Initial content

=================================== FAILURES ===================================
Test failure content here"""

    result = remove_pytest_sections(log)
    print("Result:")
    print(repr(result))
    print("\nExpected:")
    print(repr(expected))
    print(f"\nMatch: {result == expected}")

if __name__ == "__main__":
    test_warnings_summary()

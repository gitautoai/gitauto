#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the specific case that was failing
test_log = """Some content before
=========================== warnings summary ============================
warning content
Coverage LCOV written to file coverage/lcov.info
=========================== short test summary info ============================
summary content"""

result = remove_pytest_sections(test_log)
print("Result:")
print(repr(result))
print("\nExpected:")
expected = """Some content before

=========================== short test summary info ============================
summary content"""
print(repr(expected))
print(f"\nMatch: {result == expected}")

# Test the coverage line detection
test_line = "Coverage LCOV written to file coverage/lcov.info"
pytest_keywords = ['platform', 'collected', 'items', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED',
                 'warning', 'test_', '.py', '::', '[', '%]', 'cachedir', 'rootdir', 'plugins', 'results',
                 'session', 'coverage']

line_lower = test_line.lower()
has_pytest_keyword = any(keyword.lower() in line_lower for keyword in pytest_keywords)
print(f"\nCoverage line has pytest keyword: {has_pytest_keyword}")
print(f"Keywords found: {[k for k in pytest_keywords if k.lower() in line_lower]}")

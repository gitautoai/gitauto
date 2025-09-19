#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the specific coverage line that was causing issues
test_log = """Before content
=========================== warnings summary ============================
warning content
Coverage LCOV written to file coverage/lcov.info
=========================== short test summary info ============================
summary content"""

result = remove_pytest_sections(test_log)
expected = """Before content

=========================== short test summary info ============================
summary content"""

print("Test result:")
print(repr(result))
print("\nExpected:")
print(repr(expected))
print(f"\nMatch: {result == expected}")

# Test the coverage line detection
test_line = "Coverage LCOV written to file coverage/lcov.info"
pytest_keywords = ['platform', 'collected', 'items', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED',
                 'warning', 'test_', '.py', '::', '[', '%]', 'cachedir', 'rootdir', 'plugins', 'results',
                 'session', 'coverage', 'docs:', 'pytest.org']

line_lower = test_line.lower()
has_pytest_keyword = any(keyword.lower() in line_lower for keyword in pytest_keywords)
print(f"\nCoverage line has pytest keyword: {has_pytest_keyword}")
print(f"Keywords found: {[k for k in pytest_keywords if k.lower() in line_lower]}")

# Test the coverage section line
coverage_section_line = "---------- coverage: platform linux, python 3.12.11-final-0 ----------"
print(f"\nCoverage section line starts with dash: {coverage_section_line.strip().startswith('-')}")
print(f"Coverage section line contains 'coverage:': {'coverage:' in coverage_section_line.lower()}")

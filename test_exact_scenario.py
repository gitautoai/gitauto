#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the exact scenario from the failing test
test_log = """=============================== warnings summary ===============================
services/webhook/test_webhook_handler.py::TestHandleWebhookEvent::test_handle_webhook_event_workflow_run_completed_success
  /home/runner/work/gitauto/gitauto/services/webhook/webhook_handler.py:292: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    handle_coverage_report(
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------- coverage: platform linux, python 3.12.11-final-0 ----------
Coverage LCOV written to file coverage/lcov.info

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
 +  where False = isinstance(1, bool)"""

result = remove_pytest_sections(test_log)
expected = """
=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
 +  where False = isinstance(1, bool)"""

print("Result:")
print(repr(result))
print("\nExpected:")
print(repr(expected))
print(f"\nMatch: {result == expected}")

# Test individual lines
coverage_section_line = "---------- coverage: platform linux, python 3.12.11-final-0 ----------"
coverage_line = "Coverage LCOV written to file coverage/lcov.info"

print(f"\nCoverage section line check:")
print(f"  Starts with dash: {coverage_section_line.strip().startswith('-')}")
print(f"  Contains 'coverage:': {'coverage:' in coverage_section_line.lower()}")
print(f"  Should be skipped: {coverage_section_line.strip().startswith('-') and 'coverage:' in coverage_section_line.lower()}")

print(f"\nCoverage line check:")
pytest_keywords = ['platform', 'collected', 'items', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED',
                 'warning', 'test_', '.py', '::', '[', '%]', 'cachedir', 'rootdir', 'plugins', 'results',
                 'session', 'coverage', 'docs:', 'pytest.org']
line_lower = coverage_line.lower()
has_pytest_keyword = any(keyword.lower() in line_lower for keyword in pytest_keywords)
print(f"  Has pytest keyword: {has_pytest_keyword}")
print(f"  Keywords found: {[k for k in pytest_keywords if k.lower() in line_lower]}")

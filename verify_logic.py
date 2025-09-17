from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with a simplified version of the problematic content
test_log = """Line before test session
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
collected 2900 items
services/test.py ......                                                  [ 50%]
utils/test.py .........................F

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

    def test_should_test_file_with_boolean_return_values():
>       assert isinstance(result, bool)
E       assert False

utils/files/test_should_test_file.py:534: AssertionError
=============================== warnings summary ===============================
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
 +  where False = isinstance(1, bool)
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
======= 1 failed, 2616 passed, 1 skipped, 1 warning in 78.37s (0:01:18) ========
Line after test summary"""

result = remove_pytest_sections(test_log)
print("=== RESULT ===")
print(result)

expected = """Line before test session

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

    def test_should_test_file_with_boolean_return_values():
>       assert isinstance(result, bool)
E       assert False

utils/files/test_should_test_file.py:534: AssertionError

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
 +  where False = isinstance(1, bool)
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
======= 1 failed, 2616 passed, 1 skipped, 1 warning in 78.37s (0:01:18) ========
Line after test summary"""

print("\n=== EXPECTED ===")
print(expected)
print(f"\n=== MATCH: {result == expected} ===")

if result != expected:
    result_lines = result.split('\n')
    expected_lines = expected.split('\n')
    print(f"\nResult lines: {len(result_lines)}")
    print(f"Expected lines: {len(expected_lines)}")

    for i, (r, e) in enumerate(zip(result_lines, expected_lines)):
        if r != e:
            print(f"First difference at line {i}: got {repr(r)}, expected {repr(e)}")
            break

    if len(result_lines) != len(expected_lines):
        print(f"Length difference: result has {len(result_lines)} lines, expected has {len(expected_lines)} lines")
        if len(result_lines) > len(expected_lines):
            print("Extra lines in result:")
            for i in range(len(expected_lines), len(result_lines)):
                print(f"  {i}: {repr(result_lines[i])}")
        else:
            print("Missing lines in result:")
            for i in range(len(result_lines), len(expected_lines)):
                print(f"  {i}: {repr(expected_lines[i])}")

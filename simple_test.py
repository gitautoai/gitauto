from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with the problematic sections
test_log = """Before content
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
After content"""

result = remove_pytest_sections(test_log)
print("RESULT:")
print(repr(result))
print("\nRESULT (formatted):")
print(result)

#!/usr/bin/env python3

from utils.logs.clean_logs import clean_logs

# Test the exact scenario from the failing test
test_log = """utils/files/test_should_test_file.py .........................F

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

self = <test_should_test_file.TestShouldTestFile object at 0x7f44e0106780>
mock_evaluate_condition = <MagicMock name='evaluate_condition' id='139933788682048'>
sample_file_path = 'services/calculator.py'
sample_code_content = 'class Calculator:\\n    def add(self, a, b):\\n        return a + b'

    def test_should_test_file_with_boolean_return_values(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        \"\"\"Test that function properly handles different boolean-like return values.\"\"\"
        # Test with actual boolean True
        mock_evaluate_condition.return_value = True
        result = should_test_file(sample_file_path, sample_code_content)
        assert result is True
        assert isinstance(result, bool)

        # Test with actual boolean False
        mock_evaluate_condition.return_value = False
        result = should_test_file(sample_file_path, sample_code_content)
        assert result is False
        assert isinstance(result, bool)

        # Test with truthy values that should be converted to boolean
        for truthy_value in [1, "true", "yes", [1, 2, 3], {"key": "value"}]:
            mock_evaluate_condition.return_value = truthy_value
            result = should_test_file(sample_file_path, sample_code_content)
>           assert isinstance(result, bool)
E           assert False
E            +  where False = isinstance(1, bool)

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
Error: Process completed with exit code 1."""

result = clean_logs(test_log)
expected = """utils/files/test_should_test_file.py .........................F

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

self = <test_should_test_file.TestShouldTestFile object at 0x7f44e0106780>
mock_evaluate_condition = <MagicMock name='evaluate_condition' id='139933788682048'>
sample_file_path = 'services/calculator.py'
sample_code_content = 'class Calculator:\\n    def add(self, a, b):\\n        return a + b'

    def test_should_test_file_with_boolean_return_values(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        \"\"\"Test that function properly handles different boolean-like return values.\"\"\"
        # Test with actual boolean True
        mock_evaluate_condition.return_value = True
        result = should_test_file(sample_file_path, sample_code_content)
        assert result is True
        assert isinstance(result, bool)

        # Test with actual boolean False
        mock_evaluate_condition.return_value = False
        result = should_test_file(sample_file_path, sample_code_content)
        assert result is False
        assert isinstance(result, bool)

        # Test with truthy values that should be converted to boolean
        for truthy_value in [1, "true", "yes", [1, 2, 3], {"key": "value"}]:
            mock_evaluate_condition.return_value = truthy_value
            result = should_test_file(sample_file_path, sample_code_content)
>           assert isinstance(result, bool)
E           assert False
E            +  where False = isinstance(1, bool)

utils/files/test_should_test_file.py:534: AssertionError

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
 +  where False = isinstance(1, bool)
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
======= 1 failed, 2616 passed, 1 skipped, 1 warning in 78.37s (0:01:18) ========
Error: Process completed with exit code 1."""

print("Result:")
print(repr(result))
print("\nExpected:")
print(repr(expected))
print(f"\nMatch: {result == expected}")

# Check if the coverage line is removed
if "Coverage LCOV written to file coverage/lcov.info" in result:
    print("\nERROR: Coverage line was NOT removed!")
else:
    print("\nSUCCESS: Coverage line was removed!")

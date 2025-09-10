from config import UTF8
from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_remove_pytest_sections_with_pytest_output():
    # Load the test payload
    with open(
        "payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8
    ) as f:
        original_log = f.read()

    # Remove pytest sections from the log
    cleaned_log = remove_pytest_sections(original_log)

    # Check line count reduction
    original_lines = len(original_log.split("\n"))
    cleaned_lines = len(cleaned_log.split("\n"))
    assert original_lines == 283  # Original log has 283 lines
    assert cleaned_lines == 44  # Should be exactly 44 lines after section removal

    # Check that test session header is removed
    assert "test session starts" not in cleaned_log
    assert "platform linux" not in cleaned_log
    assert "plugins: cov-6.0.0" not in cleaned_log

    # Check that test progress lines are removed
    assert "test_evaluate_condition.py ......." not in cleaned_log
    assert "[  0%]" not in cleaned_log

    # Check that warnings summary is removed
    assert "warnings summary" not in cleaned_log
    assert "RuntimeWarning: coroutine" not in cleaned_log

    # Check that important parts are kept
    assert "Run python -m pytest" in cleaned_log
    assert (
        "=================================== FAILURES ==================================="
        in cleaned_log
    )
    assert (
        "TestShouldTestFile.test_should_test_file_with_boolean_return_values"
        in cleaned_log
    )
    assert "AssertionError" in cleaned_log
    assert "short test summary info" in cleaned_log
    assert "FAILED utils/files/test_should_test_file.py" in cleaned_log


def test_remove_pytest_sections_with_empty_input():
    assert remove_pytest_sections("") == ""


def test_remove_pytest_sections_with_no_pytest_markers():
    log = "Some regular error log\nwithout pytest markers\nshould remain unchanged"
    assert remove_pytest_sections(log) == log


def test_remove_pytest_sections_removes_excessive_blank_lines():
    log = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"
    result = remove_pytest_sections(log)
    assert "\n\n\n" not in result
    assert "Line 1\n\nLine 2\n\nLine 3" == result

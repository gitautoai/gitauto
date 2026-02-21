import os
from unittest.mock import patch

from config import UTF8
from utils.logs.clean_logs import clean_logs


def test_clean_logs_circleci_pipeline():
    with open("payloads/circleci/error_pr_1161_input.txt", "r", encoding=UTF8) as f:
        raw_input = f.read()

    with open("payloads/circleci/error_pr_1161_output.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(raw_input)
    assert result == expected_output


def test_clean_logs_with_pytest_output():
    with open(
        "payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8
    ) as f:
        original_log = f.read()

    with open(
        "payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8
    ) as f:
        expected_output = f.read()

    result = clean_logs(original_log)
    assert result == expected_output


def test_clean_logs_with_eslint_warnings():
    payload_path = os.path.join(
        os.path.dirname(__file__), "../../payloads/circleci/eslint_build_log.txt"
    )
    cleaned_path = os.path.join(
        os.path.dirname(__file__),
        "../../payloads/circleci/eslint_build_log_cleaned.txt",
    )

    with open(payload_path, "r", encoding=UTF8) as f:
        test_log = f.read()

    with open(cleaned_path, "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(test_log)
    assert result == expected_output


def test_clean_logs_jest_with_summary_section():
    """Test that Jest logs with 'Summary of all failing tests' are minimized correctly."""
    with open("payloads/circleci/error_usage_9744_raw.txt", "r", encoding=UTF8) as f:
        raw_input = f.read()

    with open(
        "payloads/circleci/error_usage_9744_minimized.txt", "r", encoding=UTF8
    ) as f:
        expected_output = f.read()

    result = clean_logs(raw_input)
    assert result == expected_output


def test_clean_logs_returns_original_when_eslint_cleaning_returns_none():
    """Test that clean_logs returns the original error_log when
    remove_repetitive_eslint_warnings returns None (covers line 17, branch 16->17)."""
    original_log = "some error log content\nwith multiple lines"
    with patch(
        "utils.logs.clean_logs.remove_repetitive_eslint_warnings", return_value=None
    ):
        result = clean_logs(original_log)
    assert result == original_log


def test_clean_logs_returns_original_when_eslint_cleaning_returns_none_empty_input():
    """Test the None branch with an empty string input."""
    original_log = ""
    with patch(
        "utils.logs.clean_logs.remove_repetitive_eslint_warnings", return_value=None
    ):
        result = clean_logs(original_log)
    assert result == original_log


if __name__ == "__main__":
    test_clean_logs_circleci_pipeline()

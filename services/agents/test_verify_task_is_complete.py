# pyright: reportArgumentType=false
from typing import cast
from unittest.mock import patch

import pytest

from services.agents.verify_task_is_complete import verify_task_is_complete
from services.github.types.github_types import BaseArgs


@pytest.fixture
def base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
        },
    )


@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_task_is_complete_success_with_changes(mock_get_files, base_args):
    mock_get_files.return_value = [
        {"filename": "file1.py", "status": "modified"},
    ]

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    assert "PR has changes" in result["message"]
    mock_get_files.assert_called_once_with(
        owner="test-owner", repo="test-repo", pull_number=123, token="test-token"
    )


@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_task_is_complete_failure_no_changes(mock_get_files, base_args):
    mock_get_files.return_value = []

    result = verify_task_is_complete(base_args)

    assert result["success"] is False
    assert "no changes" in result["message"]


@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_task_is_complete_no_pull_number_returns_default(mock_get_files):
    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": None,
            "token": "test-token",
        },
    )

    result = verify_task_is_complete(args)

    assert result["success"] is True
    assert result["message"] == "Task completed."
    mock_get_files.assert_not_called()


@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_task_is_complete_no_pull_number_with_issue_returns_default(
    mock_get_files,
):
    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "issue_number": 456,
            "token": "test-token",
        },
    )

    result = verify_task_is_complete(args)

    assert result["success"] is True
    assert result["message"] == "Task completed."
    mock_get_files.assert_not_called()


@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_task_is_complete_api_error_returns_default(mock_get_files, base_args):
    mock_get_files.side_effect = RuntimeError("API error")

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    assert result["message"] == "Task completed."


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_detects_missing_braces_in_test_file(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('Button', () => {
  it('renders', () => {
    expect(true).toBe(true);

  it('clicks', () => {
    expect(true).toBe(true);
  });
});"""

    result = verify_task_is_complete(base_args)

    assert result["success"] is False
    assert "Syntax errors detected" in result["message"]
    assert "Missing '});'" in result["message"]
    assert "line 2" in result["message"]


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_passes_with_correct_test_syntax(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('Button', () => {
  it('renders', () => {
    expect(true).toBe(true);
  });
});"""

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    assert "PR has changes" in result["message"]


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_ignores_non_test_files(mock_get_files, mock_get_raw, base_args):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.tsx", "status": "modified"},
    ]

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    mock_get_raw.assert_not_called()


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_ignores_removed_test_files(mock_get_files, mock_get_raw, base_args):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "removed"},
    ]

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    mock_get_raw.assert_not_called()


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_checks_both_ts_test_files(mock_get_files, mock_get_raw, base_args):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "src/Input.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    assert mock_get_raw.call_count == 2


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_checks_only_ts_when_mixed_with_py(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "tests/test_utils.py", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    assert mock_get_raw.call_count == 1


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_ignores_all_non_js_test_files(mock_get_files, mock_get_raw, base_args):
    mock_get_files.return_value = [
        {"filename": "tests/test_utils.py", "status": "modified"},
        {"filename": "tests/UtilsTest.php", "status": "modified"},
    ]

    result = verify_task_is_complete(base_args)

    assert result["success"] is True
    mock_get_raw.assert_not_called()


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_fails_when_one_of_two_ts_files_has_missing_braces(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "src/Input.test.tsx", "status": "modified"},
    ]
    correct_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    broken_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  it('other', () => {
    expect(true).toBe(true);
  });
});"""
    mock_get_raw.side_effect = [correct_content, broken_content]

    result = verify_task_is_complete(base_args)

    assert result["success"] is False
    assert "Input.test.tsx" in result["message"]
    assert "Button.test.tsx" not in result["message"]


@patch("services.agents.verify_task_is_complete.get_raw_content")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
def test_verify_fails_for_ts_with_missing_braces_ignores_py(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "tests/test_utils.py", "status": "modified"},
    ]
    broken_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  it('other', () => {
    expect(true).toBe(true);
  });
});"""
    mock_get_raw.return_value = broken_content

    result = verify_task_is_complete(base_args)

    assert result["success"] is False
    assert "Button.test.tsx" in result["message"]
    assert mock_get_raw.call_count == 1

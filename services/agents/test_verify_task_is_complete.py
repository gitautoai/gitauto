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

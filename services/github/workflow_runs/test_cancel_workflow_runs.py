from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs


@pytest.fixture
def mock_workflow_runs():
    """Fixture providing sample workflow runs data."""
    return [
        {"id": 1001, "status": "queued", "name": "CI", "head_sha": "abc123"},
        {"id": 1002, "status": "in_progress", "name": "Deploy", "head_sha": "abc123"},
        {"id": 1003, "status": "completed", "name": "Test", "head_sha": "abc123"},
        {"id": 1004, "status": "pending", "name": "Build", "head_sha": "abc123"},
        {"id": 1005, "status": "waiting", "name": "Security", "head_sha": "abc123"},
        {"id": 1006, "status": "requested", "name": "Lint", "head_sha": "abc123"},
    ]


@pytest.fixture
def mock_get_workflow_runs():
    """Fixture for mocking get_workflow_runs function."""
    with patch(
        "services.github.workflow_runs.cancel_workflow_runs.get_workflow_runs"
    ) as mock:
        yield mock


@pytest.fixture
def mock_cancel_workflow_run():
    """Fixture for mocking cancel_workflow_run function."""
    with patch(
        "services.github.workflow_runs.cancel_workflow_runs.cancel_workflow_run"
    ) as mock:
        yield mock


def test_cancel_workflow_runs_success_with_commit_sha(
    mock_get_workflow_runs,
    mock_cancel_workflow_run,
    mock_workflow_runs,
    test_owner,
    test_repo,
    test_token,
):
    """Test successful cancellation of workflow runs with commit SHA."""
    # Arrange
    commit_sha = "abc123def456"
    mock_get_workflow_runs.return_value = mock_workflow_runs

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, commit_sha=commit_sha
    )

    # Assert
    mock_get_workflow_runs.assert_called_once_with(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        commit_sha=commit_sha,
        branch=None,
    )

    # Should cancel runs with cancellable statuses (5 out of 6 runs)
    assert mock_cancel_workflow_run.call_count == 5

    # Verify specific calls for cancellable runs (using kwargs since function uses keyword arguments)
    expected_run_ids = [
        1001,
        1002,
        1004,
        1005,
        1006,
    ]  # queued, in_progress, pending, waiting, requested

    actual_calls = mock_cancel_workflow_run.call_args_list
    actual_run_ids = [call.kwargs["run_id"] for call in actual_calls]

    for expected_run_id in expected_run_ids:
        assert expected_run_id in actual_run_ids

    # Verify all calls have correct owner, repo, and token
    for call in actual_calls:
        assert call.kwargs["owner"] == test_owner
        assert call.kwargs["repo"] == test_repo
        assert call.kwargs["token"] == test_token

    assert result is None


def test_cancel_workflow_runs_success_with_branch(
    mock_get_workflow_runs,
    mock_cancel_workflow_run,
    mock_workflow_runs,
    test_owner,
    test_repo,
    test_token,
):
    """Test successful cancellation of workflow runs with branch."""
    # Arrange
    branch = "feature/test-branch"
    mock_get_workflow_runs.return_value = mock_workflow_runs

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, branch=branch
    )

    # Assert
    mock_get_workflow_runs.assert_called_once_with(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        commit_sha=None,
        branch=branch,
    )

    assert mock_cancel_workflow_run.call_count == 5
    assert result is None


def test_cancel_workflow_runs_no_workflow_runs(
    mock_get_workflow_runs, mock_cancel_workflow_run, test_owner, test_repo, test_token
):
    """Test behavior when no workflow runs are returned."""
    # Arrange
    mock_get_workflow_runs.return_value = []

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, commit_sha="abc123"
    )

    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None


def test_cancel_workflow_runs_no_cancellable_runs(
    mock_get_workflow_runs, mock_cancel_workflow_run, test_owner, test_repo, test_token
):
    """Test behavior when no workflow runs have cancellable statuses."""
    # Arrange
    non_cancellable_runs = [
        {"id": 1001, "status": "completed"},
        {"id": 1002, "status": "cancelled"},
        {"id": 1003, "status": "failure"},
        {"id": 1004, "status": "success"},
    ]
    mock_get_workflow_runs.return_value = non_cancellable_runs

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, commit_sha="abc123"
    )

    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None


def test_cancel_workflow_runs_get_workflow_runs_exception(
    mock_get_workflow_runs, mock_cancel_workflow_run, test_owner, test_repo, test_token
):
    """Test handling when get_workflow_runs raises an exception."""
    # Arrange
    http_error = requests.HTTPError("API Error")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 500
    mock_error_response.reason = "Internal Server Error"
    mock_error_response.text = "API Error"
    http_error.response = mock_error_response
    mock_get_workflow_runs.side_effect = http_error

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, commit_sha="abc123"
    )

    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None  # Due to @handle_exceptions decorator


def test_cancel_workflow_runs_cancel_workflow_run_exception(
    mock_get_workflow_runs, mock_cancel_workflow_run, test_owner, test_repo, test_token
):
    """Test that processing continues when cancel_workflow_run encounters errors."""
    # Arrange
    cancellable_runs = [
        {"id": 1001, "status": "queued"},
        {"id": 1002, "status": "in_progress"},
    ]
    mock_get_workflow_runs.return_value = cancellable_runs
    # Simulate the @handle_exceptions decorator behavior - exceptions are caught and None is returned
    mock_cancel_workflow_run.return_value = None

    # Act
    result = cancel_workflow_runs(
        owner=test_owner, repo=test_repo, token=test_token, commit_sha="abc123"
    )

    # Assert
    mock_get_workflow_runs.assert_called_once()
    assert mock_cancel_workflow_run.call_count == 2
    assert result is None


def test_cancel_workflow_runs_with_both_commit_sha_and_branch(
    mock_get_workflow_runs,
    mock_cancel_workflow_run,
    mock_workflow_runs,
    test_owner,
    test_repo,
    test_token,
):
    """Test behavior when both commit_sha and branch are provided."""
    # Arrange
    commit_sha = "abc123def456"
    branch = "feature/test-branch"
    mock_get_workflow_runs.return_value = mock_workflow_runs

    # Act
    result = cancel_workflow_runs(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        commit_sha=commit_sha,
        branch=branch,
    )

    # Assert
    # Should pass both parameters to get_workflow_runs
    mock_get_workflow_runs.assert_called_once_with(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        commit_sha=commit_sha,
        branch=branch,
    )

    assert mock_cancel_workflow_run.call_count == 5
    assert result is None

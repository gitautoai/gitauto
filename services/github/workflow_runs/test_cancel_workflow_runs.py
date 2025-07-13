from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def mock_workflow_runs():
    """Fixture providing sample workflow runs data."""
    return [
        {
            "id": 1001,
            "status": "queued",
            "name": "CI",
            "head_sha": "abc123"
        },
        {
            "id": 1002,
            "status": "in_progress",
            "name": "Deploy",
            "head_sha": "abc123"
        },
        {
            "id": 1003,
            "status": "completed",
            "name": "Test",
            "head_sha": "abc123"
        },
        {
            "id": 1004,
            "status": "pending",
            "name": "Build",
            "head_sha": "abc123"
        },
        {
            "id": 1005,
            "status": "waiting",
            "name": "Security",
            "head_sha": "abc123"
        },
        {
            "id": 1006,
            "status": "requested",
            "name": "Lint",
            "head_sha": "abc123"
        }
    ]


@pytest.fixture
def mock_get_workflow_runs():
    """Fixture for mocking get_workflow_runs function."""
    with patch("services.github.workflow_runs.cancel_workflow_runs.get_workflow_runs") as mock:
        yield mock


@pytest.fixture
def mock_cancel_workflow_run():
    """Fixture for mocking cancel_workflow_run function."""
    with patch("services.github.workflow_runs.cancel_workflow_runs.cancel_workflow_run") as mock:
        yield mock


def test_cancel_workflow_runs_success_with_commit_sha(
    mock_get_workflow_runs, mock_cancel_workflow_run, mock_workflow_runs
):
    """Test successful cancellation of workflow runs with commit SHA."""
    # Arrange
    commit_sha = "abc123def456"
    mock_get_workflow_runs.return_value = mock_workflow_runs
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha=commit_sha
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once_with(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha=commit_sha,
        branch=None
    )
    
    # Should cancel runs with cancellable statuses (5 out of 6 runs)
    assert mock_cancel_workflow_run.call_count == 5
    
    # Verify specific calls for cancellable runs
    expected_calls = [
        (OWNER, REPO, 1001, TOKEN),  # queued
        (OWNER, REPO, 1002, TOKEN),  # in_progress
        (OWNER, REPO, 1004, TOKEN),  # pending
        (OWNER, REPO, 1005, TOKEN),  # waiting
        (OWNER, REPO, 1006, TOKEN),  # requested
    ]
    
    actual_calls = [call.args for call in mock_cancel_workflow_run.call_args_list]
    for expected_call in expected_calls:
        assert expected_call in actual_calls
    
    assert result is None


def test_cancel_workflow_runs_success_with_branch(
    mock_get_workflow_runs, mock_cancel_workflow_run, mock_workflow_runs
):
    """Test successful cancellation of workflow runs with branch."""
    # Arrange
    branch = "feature/test-branch"
    mock_get_workflow_runs.return_value = mock_workflow_runs
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        branch=branch
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once_with(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha=None,
        branch=branch
    )
    
    assert mock_cancel_workflow_run.call_count == 5
    assert result is None


def test_cancel_workflow_runs_no_workflow_runs(
    mock_get_workflow_runs, mock_cancel_workflow_run
):
    """Test behavior when no workflow runs are returned."""
    # Arrange
    mock_get_workflow_runs.return_value = []
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha="abc123"
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None


def test_cancel_workflow_runs_no_cancellable_runs(
    mock_get_workflow_runs, mock_cancel_workflow_run
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
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha="abc123"
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None


def test_cancel_workflow_runs_get_workflow_runs_exception(
    mock_get_workflow_runs, mock_cancel_workflow_run
):
    """Test handling when get_workflow_runs raises an exception."""
    # Arrange
    mock_get_workflow_runs.side_effect = requests.HTTPError("API Error")
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha="abc123"
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once()
    mock_cancel_workflow_run.assert_not_called()
    assert result is None  # Due to @handle_exceptions decorator


def test_cancel_workflow_runs_cancel_workflow_run_exception(
    mock_get_workflow_runs, mock_cancel_workflow_run
):
    """Test handling when cancel_workflow_run raises an exception."""
    # Arrange
    cancellable_runs = [
        {"id": 1001, "status": "queued"},
        {"id": 1002, "status": "in_progress"},
    ]
    mock_get_workflow_runs.return_value = cancellable_runs
    mock_cancel_workflow_run.side_effect = requests.HTTPError("Cancel failed")
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha="abc123"
    )
    
    # Assert
    mock_get_workflow_runs.assert_called_once()
    assert mock_cancel_workflow_run.call_count == 2
    assert result is None


def test_cancel_workflow_runs_with_both_commit_sha_and_branch(
    mock_get_workflow_runs, mock_cancel_workflow_run, mock_workflow_runs
):
    """Test behavior when both commit_sha and branch are provided."""
    # Arrange
    commit_sha = "abc123def456"
    branch = "feature/test-branch"
    mock_get_workflow_runs.return_value = mock_workflow_runs
    
    # Act
    result = cancel_workflow_runs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha=commit_sha,
        branch=branch
    )
    
    # Assert
    # Should pass both parameters to get_workflow_runs
    mock_get_workflow_runs.assert_called_once_with(
        owner=OWNER,
        repo=REPO,
        token=TOKEN,
        commit_sha=commit_sha,
        branch=branch
    )
    
    assert mock_cancel_workflow_run.call_count == 5
    assert result is None

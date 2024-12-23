import pytest
from unittest.mock import patch
from services.github.branch_manager import get_default_branch

@patch('services.github.branch_manager.requests.get')
@patch('services.github.branch_manager.create_headers')
def test_get_default_branch(mock_create_headers, mock_requests_get):
    # Arrange
    owner = "test_owner"
    repo = "test_repo"
    token = "test_token"
    expected_branch_name = "main"
    expected_commit_sha = "abc123"
    mock_create_headers.return_value = {"Authorization": f"token {token}"}
    mock_requests_get.return_value.json.return_value = [
        {"name": expected_branch_name, "commit": {"sha": expected_commit_sha}}
    ]
    mock_requests_get.return_value.raise_for_status = lambda: None

    # Act
    branch_name, commit_sha = get_default_branch(owner, repo, token)

    # Assert
    assert branch_name == expected_branch_name
    assert commit_sha == expected_commit_sha
    mock_create_headers.assert_called_once_with(token=token)
    mock_requests_get.assert_called_once_with(
        url=f"https://api.github.com/repos/{owner}/{repo}/branches",
        headers={"Authorization": f"token {token}"},
        timeout=10
    )

def test_get_default_branch_handles_exceptions():
    # Arrange
    owner = "test_owner"
    repo = "test_repo"
    token = "test_token"

    # Act & Assert
    assert get_default_branch(owner, repo, token) == ("main", None)

import pytest
from unittest.mock import patch, MagicMock
from services.github.repo_manager import is_repo_forked

@patch('services.github.repo_manager.get')
@patch('services.github.repo_manager.create_headers')
def test_is_repo_forked(mock_create_headers, mock_get):
    """Test is_repo_forked function with forked and non-forked scenarios."""
    # Setup
    mock_create_headers.return_value = {"Authorization": "token mock-token"}

    # Mock Forked
    forked_response = MagicMock()
    forked_response.json.return_value = {"fork": True}
    forked_response.raise_for_status.return_value = None

    # Mock Non-forked
    non_forked_response = MagicMock()
    non_forked_response.json.return_value = {"fork": False}
    non_forked_response.raise_for_status.return_value = None

    # Test forked scenario
# run this file locally with: python -m tests.test_github_manager
    mock_get.return_value = forked_response
    assert is_repo_forked("someowner", "somerepo", "mock-token") is True
    # Test non-forked scenario
    mock_get.return_value = non_forked_response
    assert is_repo_forked("someowner", "somerepo", "mock-token") is False

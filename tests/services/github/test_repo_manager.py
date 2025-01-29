import pytest
from unittest.mock import patch
from services.github.repo_manager import is_repo_forked


@patch('services.github.repo_manager.get')
@patch('services.github.repo_manager.create_headers')
def test_is_repo_forked(mock_create_headers, mock_get):
    # Mock the headers
    mock_create_headers.return_value = {}

    # Test when the repository is a fork
    mock_get.return_value.json.return_value = {"fork": True}
    mock_get.return_value.raise_for_status = lambda: None
    assert is_repo_forked('owner', 'repo', 'token') is True

    # Test when the repository is not a fork
    mock_get.return_value.json.return_value = {"fork": False}
    assert is_repo_forked('owner', 'repo', 'token') is False


from unittest.mock import patch
from services.github.repo_manager import is_repo_forked

@patch('services.github.repo_manager.get')
@patch('services.github.repo_manager.create_headers')
def test_is_repo_forked(mock_create_headers, mock_get):
    # Mock the headers
    mock_create_headers.return_value = {'Authorization': 'token testtoken'}

    # Mock the response for a forked repo
    mock_get.return_value.json.return_value = {'fork': True}
    mock_get.return_value.raise_for_status = lambda: None
    assert is_repo_forked('owner', 'repo', 'testtoken') is True

    # Mock the response for a non-forked repo
    mock_get.return_value.json.return_value = {'fork': False}
    assert is_repo_forked('owner', 'repo', 'testtoken') is False

    # Ensure the correct URL was called
    mock_get.assert_called_with(url='https://api.github.com/repos/owner/repo', headers={'Authorization': 'token testtoken'}, timeout=10)

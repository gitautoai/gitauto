from unittest.mock import patch
import pytest
from unittest.mock import patch
from services.github.branch_manager import get_default_branch


@patch('services.github.branch_manager.requests.get')
@patch('services.github.branch_manager.create_headers')
def test_get_default_branch(mock_create_headers, mock_requests_get):
    # Arrange
    owner = 'test_owner'
    repo = 'test_repo'
    token = 'test_token'
    expected_branch_name = 'main'
    expected_commit_sha = 'abc123'
    mock_create_headers.return_value = {'Authorization': f'token {token}'}
    mock_response = mock_requests_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "name": expected_branch_name,
            "commit": {
                "sha": expected_commit_sha
            }
        }
    ]

    # Act
    branch_name, commit_sha = get_default_branch(owner, repo, token)

    # Assert
    assert branch_name == expected_branch_name
    assert commit_sha == expected_commit_sha
    mock_create_headers.assert_called_once_with(token=token)
    mock_requests_get.assert_called_once_with(
        url=f'https://api.github.com/repos/{owner}/{repo}/branches',
        headers={'Authorization': f'token {token}'},
        timeout=10  # Assuming TIMEOUT is set to 10
    )

    mock_response.raise_for_status.assert_called_once()
from config import GITHUB_API_URL, GITHUB_API_VERSION, GITHUB_APP_NAME, TIMEOUT
from services.github.branch_manager import get_default_branch
from tests.constants import OWNER, REPO, TOKEN


@patch("requests.get")
def test_get_default_branch(mock_get):
    # Mock response data
    mock_response = {"name": "main", "commit": {"sha": "abc123"}}
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [mock_response]

    # Call the function
    default_branch, commit_sha = get_default_branch(OWNER, REPO, TOKEN)

    # Assertions
    assert default_branch == "main"
    assert commit_sha == "abc123"
    mock_get.assert_called_once_with(
        url=f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/branches",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": GITHUB_APP_NAME,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
        timeout=TIMEOUT,
    )

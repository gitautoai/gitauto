from unittest.mock import patch
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


@patch("requests.get")
def test_get_default_branch_http_error(mock_get):
    # Mock an HTTP error response
    mock_get.return_value.status_code = 404
    mock_get.return_value.json.return_value = {"message": "Not Found"}

    # Call the function and assert it raises an HTTPException
    try:
        get_default_branch(OWNER, REPO, TOKEN)
    except Exception as e:
        assert isinstance(e, Exception)
        assert str(e) == "HTTP Error: 404 - Not Found"

from unittest.mock import patch, call, MagicMock
from requests import Response
from config import GITHUB_API_URL, GITHUB_API_VERSION, GITHUB_APP_NAME, TIMEOUT
from services.github.branch_manager import get_default_branch
from tests.constants import OWNER, REPO, TOKEN


@patch("requests.get")
def test_get_default_branch(mock_get: MagicMock) -> None:
    # Mock response data for both API calls
    mock_repo_response: dict[str, str] = {"default_branch": "main"}
    mock_branch_response: dict[str, dict[str, str]] = {"commit": {"sha": "abc123"}}

    # Create a properly typed mock response
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json = MagicMock(
        side_effect=[mock_repo_response, mock_branch_response]
    )

    mock_get.return_value = mock_response

    # Call the function
    default_branch, commit_sha = get_default_branch(OWNER, REPO, TOKEN)

    # Assertions
    assert default_branch == "main"
    assert commit_sha == "abc123"
    assert mock_get.call_count == 2

    # Verify both API calls were made with correct URLs and headers
    mock_get.assert_has_calls(
        [
            call(
                url=f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Bearer {TOKEN}",
                    "User-Agent": GITHUB_APP_NAME,
                    "X-GitHub-Api-Version": GITHUB_API_VERSION,
                },
                timeout=TIMEOUT,
            ),
            call(
                url=f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/branches/main",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Bearer {TOKEN}",
                    "User-Agent": GITHUB_APP_NAME,
                    "X-GitHub-Api-Version": GITHUB_API_VERSION,
                },
                timeout=TIMEOUT,
            ),
        ]
    )

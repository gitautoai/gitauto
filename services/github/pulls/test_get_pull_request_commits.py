# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.pulls.get_pull_request_commits import get_pull_request_commits


def test_get_pull_request_commits_success_single_page():
    mock_commits = [
        {
            "sha": "abc123",
            "commit": {
                "author": {"name": "Test User", "email": "test@example.com"},
                "message": "Test commit 1",
            },
        },
        {
            "sha": "def456",
            "commit": {
                "author": {
                    "name": "gitauto-ai[bot]",
                    "email": "161652217+gitauto-ai[bot]@users.noreply.github.com",
                },
                "message": "Test commit 2",
            },
        },
    ]

    with patch(
        "services.github.pulls.get_pull_request_commits.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_commits.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = mock_commits
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_pull_request_commits("owner", "repo", 123, "test_token")

        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123/commits",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()

        assert result == mock_commits
        assert len(result) == 2


def test_get_pull_request_commits_success_multiple_pages():
    page1_commits = [{"sha": f"commit{i}"} for i in range(100)]
    page2_commits = [{"sha": f"commit{i}"} for i in range(100, 150)]

    with patch(
        "services.github.pulls.get_pull_request_commits.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_commits.create_headers"
    ) as mock_headers:

        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = page1_commits
        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = page2_commits
        mock_response_page3 = MagicMock()
        mock_response_page3.json.return_value = []

        mock_get.side_effect = [
            mock_response_page1,
            mock_response_page2,
            mock_response_page3,
        ]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_pull_request_commits("owner", "repo", 456, "test_token")

        assert mock_get.call_count == 3
        assert len(result) == 150
        assert result[0] == {"sha": "commit0"}
        assert result[99] == {"sha": "commit99"}
        assert result[100] == {"sha": "commit100"}


def test_get_pull_request_commits_empty_result():
    with patch(
        "services.github.pulls.get_pull_request_commits.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_commits.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_pull_request_commits("owner", "repo", 123, "test_token")

        assert not result
        assert len(result) == 0


def test_get_pull_request_commits_http_error():
    with patch(
        "services.github.pulls.get_pull_request_commits.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_commits.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError(  # pylint: disable=no-member
            "404 Client Error"
        )
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_pull_request_commits("owner", "repo", 999, "test_token")

        assert not result


def test_get_pull_request_commits_network_error():
    with patch(
        "services.github.pulls.get_pull_request_commits.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_commits.create_headers"
    ) as mock_headers:

        mock_get.side_effect = requests.exceptions.ConnectionError(  # pylint: disable=no-member
            "Network error"
        )
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_pull_request_commits("owner", "repo", 123, "test_token")

        assert not result

# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.pulls.get_pull_request import get_pull_request


def test_get_pull_request_success():
    """Test successful pull request retrieval."""
    # Mock response data
    mock_pr_data = {
        "url": "https://api.github.com/repos/owner/repo/pulls/123",
        "id": 123456789,
        "node_id": "PR_kwDOABCDEF4ABCDEFG",
        "number": 123,
        "head": {
            "ref": "feature-branch",
            "sha": "abc123def456",
            "repo": {"id": 987654321, "name": "repo", "full_name": "owner/repo"},
        },
        "base": {
            "ref": "main",
            "sha": "def456abc123",
            "repo": {"id": 987654321, "name": "repo", "full_name": "owner/repo"},
        },
        "html_url": "https://github.com/owner/repo/pull/123",
        "diff_url": "https://github.com/owner/repo/pull/123.diff",
        "patch_url": "https://github.com/owner/repo/pull/123.patch",
        "issue_url": "https://api.github.com/repos/owner/repo/issues/123",
        "state": "open",
        "locked": False,
        "title": "Test PR",
        "user": {"login": "testuser", "id": 12345, "type": "User"},
        "body": "Test PR body",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "merge_commit_sha": None,
        "assignee": None,
        "assignees": [],
        "requested_reviewers": [],
        "requested_teams": [],
        "labels": [],
        "milestone": None,
        "draft": False,
        "commits_url": "https://api.github.com/repos/owner/repo/pulls/123/commits",
        "review_comments_url": "https://api.github.com/repos/owner/repo/pulls/123/comments",
        "review_comment_url": "https://api.github.com/repos/owner/repo/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/owner/repo/issues/123/comments",
        "statuses_url": "https://api.github.com/repos/owner/repo/statuses/abc123def456",
        "_links": {},
        "author_association": "OWNER",
        "auto_merge": None,
        "active_lock_reason": None,
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_by": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": True,
        "commits": 1,
        "additions": 10,
        "deletions": 5,
        "changed_files": 2,
    }

    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_pr_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify API call
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()

        # Verify result
        assert result == mock_pr_data
        assert result["number"] == 123
        assert result["title"] == "Test PR"


def test_get_pull_request_http_error_404():
    """Test handling of 404 HTTP error."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"

        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request("owner", "repo", 999, "test_token")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_http_error_500():
    """Test handling of 500 HTTP error."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal Server Error"

        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_network_error():
    """Test handling of network connection error."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_timeout_error():
    """Test handling of timeout error."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_url_construction():
    """Test that the URL is constructed correctly with different parameters."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 456}
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with different parameters
        get_pull_request("test-owner", "test-repo", 456, "test_token")

        # Verify URL construction
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_pull_request_headers_creation():
    """Test that headers are created correctly."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 123}
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        # Call function
        get_pull_request("owner", "repo", 123, "custom_token")

        # Verify headers creation
        mock_headers.assert_called_once_with(token="custom_token")


def test_get_pull_request_json_decode_error():
    """Test handling of JSON decode error."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_with_special_characters():
    """Test with owner/repo names containing special characters."""
    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 789}
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with special characters (though GitHub doesn't allow all special chars)
        get_pull_request("owner-name", "repo_name", 789, "test_token")

        # Verify URL construction handles the names correctly
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner-name/repo_name/pulls/789",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_pull_request_return_type_cast():
    """Test that the return value is properly cast to PullRequest type."""
    mock_pr_data = {"number": 123, "title": "Test PR", "state": "open"}

    with patch(
        "services.github.pulls.get_pull_request.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = mock_pr_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request("owner", "repo", 123, "test_token")

        # Verify the result is the same as the mock data (cast function doesn't change runtime behavior)
        assert result == mock_pr_data
        assert isinstance(result, dict)  # At runtime, it's still a dict

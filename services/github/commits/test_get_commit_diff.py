# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.commits.get_commit_diff import get_commit_diff


def test_get_commit_diff_success(test_owner, test_repo, test_token):
    """Test successful commit diff retrieval."""
    # Mock response data
    mock_commit_data = {
        "sha": "abc123def456",
        "commit": {
            "message": "Test commit message",
            "author": {
                "name": "Test Author",
                "email": "test@example.com",
                "date": "2023-01-01T00:00:00Z",
            },
        },
        "files": [
            {
                "filename": "test_file.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
                "patch": "@@ -1,5 +1,10 @@\n-old line\n+new line\n",
            },
            {
                "filename": "another_file.py",
                "status": "added",
                "additions": 20,
                "deletions": 0,
                "changes": 20,
                "patch": "@@ -0,0 +1,20 @@\n+new content\n",
            },
        ],
    }

    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify API call
        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{test_owner}/{test_repo}/commits/abc123def456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,  # Default TIMEOUT value from config.py
        )
        mock_response.raise_for_status.assert_called_once()

        # Verify result
        assert result is not None
        assert result["commit_id"] == "abc123def456"
        assert result["message"] == "Test commit message"
        assert result["author"] == {
            "name": "Test Author",
            "email": "test@example.com",
            "date": "2023-01-01T00:00:00Z",
        }
        assert len(result["files"]) == 2

        # Verify first file
        assert result["files"][0]["filename"] == "test_file.py"
        assert result["files"][0]["status"] == "modified"
        assert result["files"][0]["additions"] == 10
        assert result["files"][0]["deletions"] == 5
        assert result["files"][0]["changes"] == 15
        assert result["files"][0]["patch"] == "@@ -1,5 +1,10 @@\n-old line\n+new line\n"

        # Verify second file
        assert result["files"][1]["filename"] == "another_file.py"
        assert result["files"][1]["status"] == "added"
        assert result["files"][1]["additions"] == 20
        assert result["files"][1]["deletions"] == 0
        assert result["files"][1]["changes"] == 20
        assert result["files"][1]["patch"] == "@@ -0,0 +1,20 @@\n+new content\n"


def test_get_commit_diff_empty_files(test_owner, test_repo, test_token):
    """Test commit diff with no files changed."""
    mock_commit_data = {
        "sha": "abc123def456",
        "commit": {
            "message": "Empty commit",
            "author": {
                "name": "Test Author",
                "email": "test@example.com",
                "date": "2023-01-01T00:00:00Z",
            },
        },
        "files": [],
    }

    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        assert result["commit_id"] == "abc123def456"
        assert result["message"] == "Empty commit"
        assert len(result["files"]) == 0


def test_get_commit_diff_missing_fields(test_owner, test_repo, test_token):
    """Test commit diff with missing optional fields."""
    mock_commit_data = {
        "sha": "abc123def456",
        "commit": {
            "message": "Commit with missing fields",
            # Missing author field
        },
        "files": [
            {
                "filename": "test_file.py",
                "status": "modified",
                # Missing additions, deletions, changes
                # Missing patch
            }
        ],
    }

    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        assert result["commit_id"] == "abc123def456"
        assert result["message"] == "Commit with missing fields"
        assert result["author"] == {}  # Default empty dict for missing author
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "test_file.py"
        assert result["files"][0]["status"] == "modified"
        assert result["files"][0]["additions"] == 0  # Default value
        assert result["files"][0]["deletions"] == 0  # Default value
        assert result["files"][0]["changes"] == 0  # Default value
        assert result["files"][0]["patch"] == ""  # Default value


def test_get_commit_diff_http_error(test_owner, test_repo, test_token):
    """Test handling of HTTP error."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
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
        result = get_commit_diff(
            test_owner, test_repo, "nonexistent_commit", test_token
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_diff_network_error(test_owner, test_repo, test_token):
    """Test handling of network connection error."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_diff_timeout_error(test_owner, test_repo, test_token):
    """Test handling of timeout error."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_diff_headers_creation(test_owner, test_repo):
    """Test that headers are created correctly."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc123def456",
            "commit": {},
            "files": [],
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        get_commit_diff(test_owner, test_repo, "abc123def456", "custom_token")

        # Verify headers creation
        mock_headers.assert_called_once_with(token="custom_token")


def test_get_commit_diff_timeout_parameter(test_owner, test_repo, test_token):
    """Test that the timeout parameter is correctly used."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_commit_diff.TIMEOUT", 60
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc123def456",
            "commit": {},
            "files": [],
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify timeout parameter
        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 60


def test_get_commit_diff_url_construction():
    """Test that the URL is constructed correctly with different parameters."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "def789ghi012",
            "commit": {},
            "files": [],
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with different parameters
        get_commit_diff("test-owner", "test-repo", "def789ghi012", "test_token")

        # Verify URL construction
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/commits/def789ghi012",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_commit_diff_json_decode_error(test_owner, test_repo, test_token):
    """Test handling of JSON decode error."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_diff_with_special_characters(test_token):
    """Test with owner/repo/commit names containing special characters."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc-123_def.456",
            "commit": {},
            "files": [],
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with special characters
        get_commit_diff("owner-name", "repo_name", "abc-123_def.456", test_token)

        # Verify URL construction handles the names correctly
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner-name/repo_name/commits/abc-123_def.456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_commit_diff_custom_api_url(test_owner, test_repo, test_token):
    """Test with a custom GitHub API URL."""
    with patch(
        "services.github.commits.get_commit_diff.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_commit_diff.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_commit_diff.GITHUB_API_URL",
        "https://custom-github-api.com",
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc123def456",
            "commit": {},
            "files": [],
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with custom API URL
        get_commit_diff(test_owner, test_repo, "abc123def456", test_token)

        # Verify URL construction uses the custom API URL
        mock_get.assert_called_once_with(
            url=f"https://custom-github-api.com/repos/{test_owner}/{test_repo}/commits/abc123def456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )

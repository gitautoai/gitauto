# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.commits.get_commit import get_commit
from test_utils import create_test_base_args
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    """Fixture providing base arguments for testing."""
    return create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)


@pytest.fixture
def mock_commit_response():
    """Fixture providing a mock commit response."""
    return {
        "sha": "abc123def456",
        "tree": {
            "sha": "tree_sha_789xyz",
            "url": "https://api.github.com/repos/owner/repo/git/trees/tree_sha_789xyz",
        },
        "message": "Test commit message",
        "author": {
            "name": "Test Author",
            "email": "test@example.com",
            "date": "2023-01-01T00:00:00Z",
        },
    }


def test_get_commit_success(base_args, mock_commit_response):
    """Test successful commit retrieval returns tree SHA."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_commit(base_args, "abc123def456")

        # Verify API call
        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/abc123def456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,  # Default TIMEOUT value from config.py
        )
        mock_response.raise_for_status.assert_called_once()

        # Verify result is the tree SHA
        assert result == "tree_sha_789xyz"


def test_get_commit_headers_creation(base_args, mock_commit_response):
    """Test that headers are created correctly with the token."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        # Create base args with custom token
        custom_base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", token="custom_token_123"
        )

        get_commit(custom_base_args, "abc123def456")

        # Verify headers creation with correct token
        mock_headers.assert_called_once_with(token="custom_token_123")


def test_get_commit_url_construction(base_args, mock_commit_response):
    """Test that the URL is constructed correctly with different parameters."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with different parameters
        custom_base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", token="test_token"
        )
        get_commit(custom_base_args, "def789ghi012")

        # Verify URL construction
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/git/commits/def789ghi012",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_commit_with_special_characters(mock_commit_response):
    """Test with owner/repo/commit names containing special characters."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with special characters
        special_base_args = create_test_base_args(
            owner="owner-name", repo="repo_name.test", token="token_123"
        )
        get_commit(special_base_args, "abc-123_def.456")

        # Verify URL construction handles the names correctly
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner-name/repo_name.test/git/commits/abc-123_def.456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_commit_timeout_parameter(base_args, mock_commit_response):
    """Test that the timeout parameter is correctly used."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers, patch("services.github.commits.get_commit.TIMEOUT", 60):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        get_commit(base_args, "abc123def456")

        # Verify timeout parameter
        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 60


def test_get_commit_custom_api_url(base_args, mock_commit_response):
    """Test with a custom GitHub API URL."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_commit.GITHUB_API_URL",
        "https://custom-github-api.com",
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        get_commit(base_args, "abc123def456")

        # Verify URL construction uses the custom API URL
        mock_get.assert_called_once_with(
            url=f"https://custom-github-api.com/repos/{OWNER}/{REPO}/git/commits/abc123def456",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_commit_different_tree_sha(base_args):
    """Test that different tree SHAs are returned correctly."""
    test_cases = [
        "tree_sha_123abc",
        "another_tree_sha_456def",
        "very_long_tree_sha_789ghi012jkl345mno678pqr901stu234vwx567yz",
        "short_sha",
    ]

    for tree_sha in test_cases:
        with patch(
            "services.github.commits.get_commit.requests.get"
        ) as mock_get, patch(
            "services.github.commits.get_commit.create_headers"
        ) as mock_headers:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "sha": "commit_sha",
                "tree": {"sha": tree_sha},
            }
            mock_get.return_value = mock_response
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            result = get_commit(base_args, "commit_sha")
            assert result == tree_sha


def test_get_commit_http_error_404(base_args):
    """Test handling of 404 HTTP error."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
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
        result = get_commit(base_args, "nonexistent_commit")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_http_error_403(base_args):
    """Test handling of 403 HTTP error (forbidden)."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Forbidden"

        http_error = requests.exceptions.HTTPError("403 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "forbidden_commit")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_network_error(base_args):
    """Test handling of network connection error."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "abc123def456")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_timeout_error(base_args):
    """Test handling of timeout error."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "abc123def456")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_json_decode_error(base_args):
    """Test handling of JSON decode error."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "abc123def456")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_key_error_missing_tree(base_args):
    """Test handling of missing tree key in response."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc123def456",
            # Missing "tree" key
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "abc123def456")

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_commit_key_error_missing_tree_sha(base_args):
    """Test handling of missing sha key in tree object."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sha": "abc123def456",
            "tree": {
                # Missing "sha" key
                "url": "https://api.github.com/repos/owner/repo/git/trees/tree_sha"
            },
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_commit(base_args, "abc123def456")

        # Verify result is None (default_return_value from decorator)
        assert result is None


@pytest.mark.parametrize(
    "commit_sha",
    [
        "abc123def456",
        "1234567890abcdef",
        "short",
        "very_long_commit_sha_with_underscores_and_numbers_123456789",
        "commit-with-dashes",
        "commit.with.dots",
    ],
)
def test_get_commit_various_commit_sha_formats(
    base_args, mock_commit_response, commit_sha
):
    """Test that the function handles various commit SHA formats correctly."""
    with patch("services.github.commits.get_commit.requests.get") as mock_get, patch(
        "services.github.commits.get_commit.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_commit_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        result = get_commit(base_args, commit_sha)

        # Verify the commit SHA is correctly used in the URL
        expected_url = (
            f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/{commit_sha}"
        )
        mock_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )

        # Verify result is the tree SHA
        assert result == "tree_sha_789xyz"

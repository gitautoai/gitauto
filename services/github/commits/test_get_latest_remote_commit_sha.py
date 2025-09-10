# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)


@pytest.fixture
def base_args(test_owner, test_repo, test_token, create_test_base_args):
    """Fixture providing base arguments for testing."""
    return create_test_base_args(
        owner=test_owner, repo=test_repo, token=test_token, base_branch="main"
    )


@pytest.fixture
def mock_successful_response():
    """Fixture providing a mock successful GitHub API response."""
    return {"object": {"sha": "abc123def456789ghi012jkl345mno678pqr901st"}}


@pytest.fixture
def mock_empty_repo_response():
    """Fixture providing a mock response for empty repository."""
    return {"message": "Git Repository is empty."}


def test_get_latest_remote_commit_sha_success(base_args, mock_successful_response):
    """Test successful retrieval of latest remote commit SHA."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)

        # Verify API call
        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{base_args['owner']}/{base_args['repo']}/git/ref/heads/{base_args['base_branch']}",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()

        # Verify result is the commit SHA
        assert result == "abc123def456789ghi012jkl345mno678pqr901st"


def test_get_latest_remote_commit_sha_headers_creation(
    mock_successful_response, create_test_base_args
):
    """Test that headers are created correctly with the token."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        # Create base args with custom token
        custom_base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", token="custom_token_123", base_branch="main"
        )

        get_latest_remote_commit_sha("https://github.com/owner/repo.git", custom_base_args)

        # Verify headers creation with correct token
        mock_headers.assert_called_once_with(token="custom_token_123")


def test_get_latest_remote_commit_sha_url_construction(
    mock_successful_response, create_test_base_args
):
    """Test that the URL is constructed correctly with different parameters."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with different parameters
        custom_base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", token="test_token", base_branch="develop"
        )
        get_latest_remote_commit_sha("https://github.com/owner/repo.git", custom_base_args)

        # Verify URL construction
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/git/ref/heads/develop",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_latest_remote_commit_sha_with_special_characters(
    mock_successful_response, create_test_base_args
):
    """Test with owner/repo/branch names containing special characters."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with special characters
        special_base_args = create_test_base_args(
            owner="owner-name", repo="repo_name.test", token="token_123", base_branch="feature/test-branch"
        )
        get_latest_remote_commit_sha("https://github.com/owner/repo.git", special_base_args)

        # Verify URL construction handles the names correctly
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner-name/repo_name.test/git/ref/heads/feature/test-branch",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_latest_remote_commit_sha_timeout_parameter(base_args, mock_successful_response):
    """Test that the timeout parameter is correctly used."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.TIMEOUT", 60
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)

        # Verify timeout parameter
        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 60


def test_get_latest_remote_commit_sha_custom_api_url(base_args, mock_successful_response):
    """Test with a custom GitHub API URL."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.GITHUB_API_URL",
        "https://custom-github-api.com",
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)

        # Verify URL construction uses the custom API URL
        mock_get.assert_called_once_with(
            url=f"https://custom-github-api.com/repos/{base_args['owner']}/{base_args['repo']}/git/ref/heads/{base_args['base_branch']}",
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )


def test_get_latest_remote_commit_sha_different_commit_shas(base_args):
    """Test that different commit SHAs are returned correctly."""
    test_cases = [
        "abc123def456789ghi012jkl345mno678pqr901st",
        "1234567890abcdef1234567890abcdef12345678",
        "short_sha_123",
        "very_long_commit_sha_with_underscores_and_numbers_123456789abcdef",
    ]

    for commit_sha in test_cases:
        with patch(
            "services.github.commits.get_latest_remote_commit_sha.requests.get"
        ) as mock_get, patch(
            "services.github.commits.get_latest_remote_commit_sha.create_headers"
        ) as mock_headers:
            mock_response = MagicMock()
            mock_response.json.return_value = {"object": {"sha": commit_sha}}
            mock_get.return_value = mock_response
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            result = get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
            assert result == commit_sha


def test_get_latest_remote_commit_sha_empty_repository_409_error(base_args, mock_empty_repo_response):
    """Test handling of 409 error for empty repository."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.initialize_repo"
    ) as mock_initialize, patch(
        "services.github.commits.get_latest_remote_commit_sha.logging.info"
    ) as mock_logging:
        # Setup mocks for first call (409 error) and second call (success)
        mock_response_409 = MagicMock()
        mock_response_409.status_code = 409
        mock_response_409.json.return_value = mock_empty_repo_response
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"object": {"sha": "new_commit_sha_123"}}
        
        http_error = requests.exceptions.HTTPError("409 Client Error")
        http_error.response = mock_response_409
        
        # First call raises 409, second call succeeds
        mock_get.side_effect = [
            MagicMock(raise_for_status=MagicMock(side_effect=http_error)),
            mock_response_success
        ]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        clone_url = "https://github.com/owner/repo.git"
        result = get_latest_remote_commit_sha(clone_url, base_args)

        # Verify initialize_repo was called
        expected_repo_path = f"/tmp/repo/{base_args['owner']}-{base_args['repo']}"
        mock_initialize.assert_called_once_with(
            repo_path=expected_repo_path, remote_url=clone_url, token=base_args["token"]
        )
        
        # Verify logging message
        mock_logging.assert_called_once_with("Repository is empty. So, creating an initial empty commit.")
        
        # Verify function was called twice (recursive call)
        assert mock_get.call_count == 2
        
        # Verify result from second call
        assert result == "new_commit_sha_123"


def test_get_latest_remote_commit_sha_409_error_different_message(base_args):
    """Test handling of 409 error with different message (not empty repo)."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"message": "Different conflict message"}

        http_error = requests.exceptions.HTTPError("409 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise the HTTPError since it's not empty repo
        with pytest.raises(requests.exceptions.HTTPError):
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)


def test_get_latest_remote_commit_sha_http_error_404(base_args):
    """Test handling of 404 HTTP error."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
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

        # Call function - should raise HTTPError due to raise_on_error=True
        with pytest.raises(requests.exceptions.HTTPError):
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)


def test_get_latest_remote_commit_sha_http_error_403(base_args):
    """Test handling of 403 HTTP error (forbidden)."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"


def test_get_latest_remote_commit_sha_network_error(base_args):
    """Test handling of network connection error."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.update_comment"
    ) as mock_update_comment:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise RuntimeError due to Exception handling
        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
        
        # Verify error message
        assert "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha" in str(exc_info.value)
        
        # Verify update_comment was called
        mock_update_comment.assert_called_once()
        call_args = mock_update_comment.call_args
        assert "get_latest_remote_commit_sha encountered an error" in call_args.kwargs["body"]
        assert call_args.kwargs["base_args"] == base_args


def test_get_latest_remote_commit_sha_timeout_error(base_args):
    """Test handling of timeout error."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.update_comment"
    ) as mock_update_comment:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise RuntimeError due to Exception handling
        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
        
        # Verify error message
        assert "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha" in str(exc_info.value)
        
        # Verify update_comment was called
        mock_update_comment.assert_called_once()


def test_get_latest_remote_commit_sha_json_decode_error(base_args):
    """Test handling of JSON decode error."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.update_comment"
    ) as mock_update_comment:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise RuntimeError due to Exception handling
        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
        
        # Verify error message
        assert "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha" in str(exc_info.value)
        
        # Verify update_comment was called
        mock_update_comment.assert_called_once()


def test_get_latest_remote_commit_sha_key_error_missing_object(base_args):
    """Test handling of missing object key in response."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.update_comment"
    ) as mock_update_comment:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {
            # Missing "object" key
            "ref": "refs/heads/main"
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise RuntimeError due to Exception handling
        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
        
        # Verify error message
        assert "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha" in str(exc_info.value)
        
        # Verify update_comment was called
        mock_update_comment.assert_called_once()


def test_get_latest_remote_commit_sha_key_error_missing_sha(base_args):
    """Test handling of missing sha key in object."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.update_comment"
    ) as mock_update_comment:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": {
                # Missing "sha" key
                "type": "commit",
                "url": "https://api.github.com/repos/owner/repo/git/commits/abc123"
            }
        }
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should raise RuntimeError due to Exception handling
        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha("https://github.com/owner/repo.git", base_args)
        
        # Verify error message
        assert "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha" in str(exc_info.value)
        
        # Verify update_comment was called
        mock_update_comment.assert_called_once()


@pytest.mark.parametrize(
    "branch_name",
    [
        "main",
        "develop",
        "feature/new-feature",
        "hotfix/bug-fix",
        "release/v1.0.0",
        "test-branch",
        "branch_with_underscores",
        "branch.with.dots",
    ],
)
def test_get_latest_remote_commit_sha_various_branch_names(
    base_args, mock_successful_response, branch_name, create_test_base_args
):
    """Test that the function handles various branch name formats correctly."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Create base args with custom branch
        custom_base_args = create_test_base_args(
            owner=base_args["owner"], 
            repo=base_args["repo"], 
            token=base_args["token"], 
            base_branch=branch_name
        )
        
        result = get_latest_remote_commit_sha("https://github.com/owner/repo.git", custom_base_args)

        # Verify the branch name is correctly used in the URL
        expected_url = f"https://api.github.com/repos/{custom_base_args['owner']}/{custom_base_args['repo']}/git/ref/heads/{branch_name}"
        mock_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test_token"},
            timeout=120,
        )

        # Verify result is the commit SHA
        assert result == "abc123def456789ghi012jkl345mno678pqr901st"


def test_get_latest_remote_commit_sha_clone_url_parameter_not_used_in_api_call(
    base_args, mock_successful_response
):
    """Test that clone_url parameter doesn't affect the API call URL construction."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Test with different clone URLs
        clone_urls = [
            "https://github.com/owner/repo.git",
            "git@github.com:owner/repo.git",
            "https://github.com/different-owner/different-repo.git",
        ]
        
        for clone_url in clone_urls:
            mock_get.reset_mock()
            get_latest_remote_commit_sha(clone_url, base_args)

            # Verify URL construction uses base_args, not clone_url
            expected_url = f"https://api.github.com/repos/{base_args['owner']}/{base_args['repo']}/git/ref/heads/{base_args['base_branch']}"
            mock_get.assert_called_once_with(
                url=expected_url,
                headers={"Authorization": "Bearer test_token"},
                timeout=120,
            )


def test_get_latest_remote_commit_sha_empty_repo_recursive_call_success(base_args):
    """Test successful recursive call after empty repository initialization."""
    with patch(
        "services.github.commits.get_latest_remote_commit_sha.requests.get"
    ) as mock_get, patch(
        "services.github.commits.get_latest_remote_commit_sha.create_headers"
    ) as mock_headers, patch(
        "services.github.commits.get_latest_remote_commit_sha.initialize_repo"
    ) as mock_initialize:
        # Setup mocks for first call (409 error) and second call (success)
        mock_response_409 = MagicMock()
        mock_response_409.status_code = 409
        mock_response_409.json.return_value = {"message": "Git Repository is empty."}
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"object": {"sha": "initialized_commit_sha"}}
        
        http_error = requests.exceptions.HTTPError("409 Client Error")
        http_error.response = mock_response_409
        
        # First call raises 409, second call succeeds
        mock_get.side_effect = [
            MagicMock(raise_for_status=MagicMock(side_effect=http_error)),
            mock_response_success
        ]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        clone_url = "https://github.com/owner/repo.git"
        result = get_latest_remote_commit_sha(clone_url, base_args)

        # Verify both API calls were made
        assert mock_get.call_count == 2
        
        # Verify result from successful second call
        assert result == "initialized_commit_sha"
        
        # Verify initialize_repo was called with correct parameters

from unittest.mock import patch, MagicMock
import pytest
import requests
import json

from services.github.branches.get_default_branch import get_default_branch


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get for successful API calls."""
    with patch("services.github.branches.get_default_branch.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.branches.get_default_branch.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def sample_repo_response():
    """Sample repository API response."""
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "default_branch": "main",
        "private": False,
    }


@pytest.fixture
def sample_branch_response():
    """Sample branch API response."""
    return {
        "name": "main",
        "commit": {
            "sha": "abc123def456789",
            "url": "https://api.github.com/repos/test-owner/test-repo/commits/abc123def456789",
        },
        "protected": False,
    }


class TestGetDefaultBranch:
    def test_successful_request(
        self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response
    ):
        """Test successful API calls returning default branch and commit SHA."""
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        result = get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify
        assert result == ("main", "abc123def456789")
        assert mock_requests_get.call_count == 2
        
        # Verify first call (repository info)
        first_call = mock_requests_get.call_args_list[0]
        assert first_call[1]["url"] == "https://api.github.com/repos/test-owner/test-repo"
        assert first_call[1]["timeout"] == 120
        
        # Verify second call (branch info)
        second_call = mock_requests_get.call_args_list[1]
        assert second_call[1]["url"] == "https://api.github.com/repos/test-owner/test-repo/branches/main"
        assert second_call[1]["timeout"] == 120
        
        # Verify headers were created
        mock_create_headers.assert_called_with(token="test-token")

    def test_different_default_branch(
        self, mock_requests_get, mock_create_headers, sample_branch_response
    ):
        """Test with a repository that has a different default branch name."""
        # Setup repo response with different default branch
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": "develop",
            "private": False,
        }
        
        # Setup branch response for develop branch
        branch_response_data = {
            "name": "develop",
            "commit": {
                "sha": "xyz789abc123456",
                "url": "https://api.github.com/repos/test-owner/test-repo/commits/xyz789abc123456",
            },
            "protected": True,
        }
        
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = branch_response_data
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        result = get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify
        assert result == ("develop", "xyz789abc123456")
        
        # Verify the branch URL was constructed correctly
        second_call = mock_requests_get.call_args_list[1]
        assert second_call[1]["url"] == "https://api.github.com/repos/test-owner/test-repo/branches/develop"

    def test_repo_api_http_error(self, mock_requests_get, mock_create_headers):
        """Test behavior when repository API call fails with HTTP error."""
        # Setup mock to raise HTTPError on first call
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = MagicMock()
        http_error.response.status_code = 404
        http_error.response.reason = "Not Found"
        http_error.response.text = "Repository not found"
        
        repo_response = MagicMock()
        repo_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = repo_response
        
        # Execute and verify exception is raised (due to raise_on_error=True)
        with pytest.raises(requests.exceptions.HTTPError):
            get_default_branch("test-owner", "nonexistent-repo", "test-token")
        
        # Verify only one call was made (to repository API)
        assert mock_requests_get.call_count == 1

    def test_branch_api_http_error(
        self, mock_requests_get, mock_create_headers, sample_repo_response
    ):
        """Test behavior when branch API call fails with HTTP error."""
        # Setup successful repo response
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        # Setup branch response to raise HTTPError
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = MagicMock()
        http_error.response.status_code = 404
        http_error.response.reason = "Not Found"
        http_error.response.text = "Branch not found"
        
        branch_response = MagicMock()
        branch_response.raise_for_status.side_effect = http_error
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute and verify exception is raised
        with pytest.raises(requests.exceptions.HTTPError):
            get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify both calls were made
        assert mock_requests_get.call_count == 2

    def test_json_decode_error_repo_response(self, mock_requests_get, mock_create_headers):
        """Test behavior when repository response has invalid JSON."""
        repo_response = MagicMock()
        repo_response.raise_for_status.return_value = None
        repo_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        mock_requests_get.return_value = repo_response
        
        # Execute and verify exception is raised
        with pytest.raises(json.JSONDecodeError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_json_decode_error_branch_response(
        self, mock_requests_get, mock_create_headers, sample_repo_response
    ):
        """Test behavior when branch response has invalid JSON."""
        # Setup successful repo response
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        # Setup branch response with JSON decode error
        branch_response = MagicMock()
        branch_response.raise_for_status.return_value = None
        branch_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute and verify exception is raised
        with pytest.raises(json.JSONDecodeError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_missing_default_branch_key(self, mock_requests_get, mock_create_headers):
        """Test behavior when repository response is missing default_branch key."""
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            # Missing "default_branch" key
            "private": False,
        }
        
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        
        mock_requests_get.return_value = repo_response
        
        # Execute and verify KeyError is raised
        with pytest.raises(KeyError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_missing_commit_sha_key(
        self, mock_requests_get, mock_create_headers, sample_repo_response
    ):
        """Test behavior when branch response is missing commit.sha key."""
        # Setup successful repo response
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        # Setup branch response missing commit.sha
        branch_response_data = {
            "name": "main",
            "commit": {
                # Missing "sha" key
                "url": "https://api.github.com/repos/test-owner/test-repo/commits/abc123def456789",
            },
            "protected": False,
        }
        
        branch_response = MagicMock()
        branch_response.json.return_value = branch_response_data
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute and verify KeyError is raised
        with pytest.raises(KeyError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_function_parameters_types(self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response):
        """Test that function accepts string parameters and returns tuple of strings."""
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute with string parameters
        result = get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify return type
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # branch name
        assert isinstance(result[1], str)  # commit SHA
        assert result[0] == "main"
        assert result[1] == "abc123def456789"

    @pytest.mark.parametrize(
        "owner,repo,expected_repo_url",
        [
            ("test-owner", "test-repo", "https://api.github.com/repos/test-owner/test-repo"),
            ("org-name", "my-project", "https://api.github.com/repos/org-name/my-project"),
            ("user123", "repo-with-dashes", "https://api.github.com/repos/user123/repo-with-dashes"),
            ("special.user", "repo_with_underscores", "https://api.github.com/repos/special.user/repo_with_underscores"),
        ],
    )
    def test_url_construction_with_various_owner_repo_names(
        self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response, owner, repo, expected_repo_url
    ):
        """Test that URLs are constructed correctly for various owner and repo name formats."""

    def test_requests_timeout_parameter(self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response):
        """Test that requests are made with correct timeout parameter."""
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify both calls used correct timeout
        for call in mock_requests_get.call_args_list:
            assert call[1]["timeout"] == 120

    def test_headers_passed_to_both_requests(self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response):
        """Test that headers are passed to both API requests."""
        expected_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        mock_create_headers.return_value = expected_headers
        
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify headers were created once and used in both calls
        mock_create_headers.assert_called_once_with(token="test-token")
        
        for call in mock_requests_get.call_args_list:
            assert call[1]["headers"] == expected_headers

    def test_raise_for_status_called_on_both_responses(self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response):
        """Test that raise_for_status is called on both response objects."""
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        get_default_branch("test-owner", "test-repo", "test-token")
        
        # Verify raise_for_status was called on both responses
        repo_response.raise_for_status.assert_called_once()
        branch_response.raise_for_status.assert_called_once()

    def test_json_called_on_both_responses(self, mock_requests_get, mock_create_headers, sample_repo_response, sample_branch_response):
        """Test that json() is called on both response objects."""
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Update sample responses to match the test parameters
        updated_repo_response = sample_repo_response.copy()

    def test_handle_exceptions_decorator_default_return_value(self, mock_requests_get, mock_create_headers):
        """Test that the handle_exceptions decorator's default return value is correctly configured."""
        # This test verifies the decorator configuration without triggering an exception
        # The decorator is configured with default_return_value=("main", "") and raise_on_error=True
        
        # Setup a successful response to verify normal operation
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": "main",
            "private": False,
        }
        
        branch_response_data = {
            "name": "main",
            "commit": {
                "sha": "abc123def456789",
                "url": "https://api.github.com/repos/test-owner/test-repo/commits/abc123def456789",
            },
            "protected": False,
        }
        
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = branch_response_data
        branch_response.raise_for_status.return_value = None
        
        updated_repo_response["name"] = repo
        updated_repo_response["full_name"] = f"{owner}/{repo}"
        
        # Setup mock responses
        repo_response = MagicMock()
        repo_response.json.return_value = updated_repo_response
        repo_response.raise_for_status.return_value = None
        
        branch_response = MagicMock()
        branch_response.json.return_value = sample_branch_response
        branch_response.raise_for_status.return_value = None
        
        mock_requests_get.side_effect = [repo_response, branch_response]
        
        # Execute
        result = get_default_branch(owner, repo, "test-token")
        
        # Verify URLs were constructed correctly
        first_call = mock_requests_get.call_args_list[0]
        assert first_call[1]["url"] == expected_repo_url
        
        second_call = mock_requests_get.call_args_list[1]
        expected_branch_url = f"{expected_repo_url}/branches/main"
        assert second_call[1]["url"] == expected_branch_url
        
        # Verify result
        assert result == ("main", "abc123def456789")

    @pytest.mark.parametrize(
        "default_branch,commit_sha",
        [
            ("main", "abc123def456789"),
            ("master", "xyz789abc123456"),
            ("develop", "123456789abcdef"),
            ("feature-branch", "fedcba987654321"),
            ("release/v1.0", "111222333444555"),
        ],
    )
    def test_various_branch_names_and_commit_shas(
        self, mock_requests_get, mock_create_headers, default_branch, commit_sha
    ):
        """Test function with various branch names and commit SHAs."""
        # Setup repo response with parameterized default branch
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": default_branch,

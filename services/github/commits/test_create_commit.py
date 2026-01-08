from unittest.mock import MagicMock, patch

import pytest
import requests

from services.github.commits.create_commit import create_commit


@pytest.fixture
def sample_base_args(create_test_base_args, test_owner, test_repo):
    return create_test_base_args(
        owner=test_owner, repo=test_repo, token="test-token-mock"
    )


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post for successful API calls."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"sha": "abc123def456789"}
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.commits.create_commit.create_headers") as mock_headers:
        mock_headers.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token-mock",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock_headers


def test_create_commit_success(
    mock_requests_post, mock_create_headers, sample_base_args
):
    """Test successful commit creation."""
    message = "Test commit message"
    tree_sha = "tree123abc"
    parent_sha = "parent456def"

    result = create_commit(sample_base_args, message, tree_sha, parent_sha)

    # Verify the function returns the commit SHA
    assert result == "abc123def456789"

    # Verify requests.post was called with correct parameters
    mock_requests_post.assert_called_once_with(
        url=f"https://api.github.com/repos/{sample_base_args['owner']}/{sample_base_args['repo']}/git/commits",
        json={"message": message, "tree": tree_sha, "parents": [parent_sha]},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {sample_base_args['token']}",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )

    # Verify create_headers was called with the token
    mock_create_headers.assert_called_once_with(token=sample_base_args["token"])

    # Verify raise_for_status was called
    mock_requests_post.return_value.raise_for_status.assert_called_once()

    # Verify json was called
    mock_requests_post.return_value.json.assert_called_once()


def test_create_commit_with_different_parameters(
    mock_requests_post, mock_create_headers, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner", repo="test-repo", token="test-token-123"
    )
    message = "Different commit message"
    tree_sha = "different_tree_sha"
    parent_sha = "different_parent_sha"

    result = create_commit(base_args, message, tree_sha, parent_sha)

    assert result == "abc123def456789"

    # Verify the correct URL was constructed
    call_args = mock_requests_post.call_args
    assert (
        call_args.kwargs["url"]
        == "https://api.github.com/repos/test-owner/test-repo/git/commits"
    )

    # Verify the correct JSON payload
    assert call_args.kwargs["json"] == {
        "message": message,
        "tree": tree_sha,
        "parents": [parent_sha],
    }

    # Verify create_headers was called with the correct token
    mock_create_headers.assert_called_once_with(token="test-token-123")


def test_create_commit_with_empty_message(mock_requests_post, sample_base_args):
    """Test commit creation with empty message."""
    message = ""
    tree_sha = "tree123abc"
    parent_sha = "parent456def"

    result = create_commit(sample_base_args, message, tree_sha, parent_sha)

    assert result == "abc123def456789"

    # Verify empty message is passed as is
    call_args = mock_requests_post.call_args
    assert call_args.kwargs["json"]["message"] == ""


def test_create_commit_with_long_message(mock_requests_post, sample_base_args):
    """Test commit creation with very long message."""
    message = "A" * 1000  # Very long commit message
    tree_sha = "tree123abc"
    parent_sha = "parent456def"

    result = create_commit(sample_base_args, message, tree_sha, parent_sha)

    assert result == "abc123def456789"

    # Verify long message is passed correctly
    call_args = mock_requests_post.call_args
    assert call_args.kwargs["json"]["message"] == message
    assert len(call_args.kwargs["json"]["message"]) == 1000


def test_create_commit_with_special_characters(mock_requests_post, sample_base_args):
    """Test commit creation with special characters in message."""
    message = "Test commit with émojis 🚀 and special chars: !@#$%^&*()"
    tree_sha = "tree123abc"
    parent_sha = "parent456def"

    result = create_commit(sample_base_args, message, tree_sha, parent_sha)

    assert result == "abc123def456789"

    # Verify special characters are preserved
    call_args = mock_requests_post.call_args
    assert call_args.kwargs["json"]["message"] == message


def test_create_commit_with_different_sha_formats(
    mock_requests_post, mock_create_headers, sample_base_args
):
    """Test commit creation with various SHA formats."""
    test_cases = [
        ("abc123", "def456"),  # Short SHAs
        ("1234567890abcdef", "fedcba0987654321"),  # Medium SHAs
        (
            "a1b2c3d4e5f6789012345678901234567890abcd",
            "f1e2d3c4b5a6789012345678901234567890fedc",
        ),  # Full SHAs
        ("0" * 40, "f" * 40),  # Edge case SHAs
    ]

    for tree_sha, parent_sha in test_cases:
        mock_requests_post.reset_mock()
        mock_create_headers.reset_mock()

        result = create_commit(sample_base_args, "Test message", tree_sha, parent_sha)
        assert result == "abc123def456789"

        # Verify SHAs are passed correctly
        call_args = mock_requests_post.call_args
        assert call_args.kwargs["json"]["tree"] == tree_sha
        assert call_args.kwargs["json"]["parents"] == [parent_sha]


def test_create_commit_http_error_handled(sample_base_args):
    """Test that HTTP errors are handled by the decorator."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"

        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        # The function should return None due to handle_exceptions decorator
        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")
        assert result is None

        # Verify the request was still made
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_create_commit_request_timeout_handled(sample_base_args):
    """Test that request timeout is handled by the decorator."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # The function should return None due to handle_exceptions decorator
        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")
        assert result is None

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_commit_connection_error_handled(sample_base_args):
    """Test that connection errors are handled by the decorator."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # The function should return None due to handle_exceptions decorator
        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")
        assert result is None

        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_commit_json_parsing_error_handled(sample_base_args):
    """Test that JSON parsing errors are handled by the decorator."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        # The function should return None due to handle_exceptions decorator
        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")
        assert result is None

        # Verify the request was made and JSON parsing was attempted
        mock_post.assert_called_once()
        mock_response.json.assert_called_once()


def test_create_commit_uses_correct_api_url(mock_requests_post, sample_base_args):
    """Test that the correct GitHub API URL is used."""
    create_commit(sample_base_args, "Test message", "tree123", "parent456")

    call_args = mock_requests_post.call_args
    expected_url = f"https://api.github.com/repos/{sample_base_args['owner']}/{sample_base_args['repo']}/git/commits"
    assert call_args.kwargs["url"] == expected_url


def test_create_commit_uses_correct_timeout(mock_requests_post, sample_base_args):
    """Test that the correct timeout value is used."""
    create_commit(sample_base_args, "Test message", "tree123", "parent456")

    call_args = mock_requests_post.call_args
    assert call_args.kwargs["timeout"] == 120


def test_create_commit_json_payload_structure(mock_requests_post, sample_base_args):
    """Test that the JSON payload has the correct structure."""
    message = "Test commit message"
    tree_sha = "tree123abc"
    parent_sha = "parent456def"

    create_commit(sample_base_args, message, tree_sha, parent_sha)

    call_args = mock_requests_post.call_args
    json_payload = call_args.kwargs["json"]

    # Verify payload structure
    assert "message" in json_payload
    assert "tree" in json_payload
    assert "parents" in json_payload
    assert len(json_payload) == 3

    # Verify payload values
    assert json_payload["message"] == message
    assert json_payload["tree"] == tree_sha
    assert json_payload["parents"] == [parent_sha]
    assert isinstance(json_payload["parents"], list)
    assert len(json_payload["parents"]) == 1


def test_create_commit_with_special_characters_in_owner_repo(
    mock_requests_post, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test-owner_123",
        repo="test.repo-name_456",
        token="test_token",
    )

    result = create_commit(base_args, "Test message", "tree123", "parent456")
    assert result == "abc123def456789"

    call_args = mock_requests_post.call_args
    expected_url = (
        "https://api.github.com/repos/test-owner_123/test.repo-name_456/git/commits"
    )
    assert call_args.kwargs["url"] == expected_url


def test_create_commit_extracts_base_args_correctly(
    mock_requests_post, create_test_base_args
):
    base_args = create_test_base_args(
        owner="extracted_owner",
        repo="extracted_repo",
        token="extracted_token",
        issue_number=123,
        sender_name="test_sender",
        new_branch="test_branch",
    )

    create_commit(base_args, "Test message", "tree123", "parent456")

    # Verify only the required fields were used
    call_args = mock_requests_post.call_args
    assert "extracted_owner" in call_args.kwargs["url"]
    assert "extracted_repo" in call_args.kwargs["url"]

    # Headers are mocked via fixtures


def test_create_commit_return_value_type(sample_base_args):
    """Test that the function returns a string SHA."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"sha": "abc123def456789"}
        mock_post.return_value = mock_response

        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")

        assert isinstance(result, str)
        assert result == "abc123def456789"


@pytest.mark.parametrize(
    "error_type,error_message",
    [
        (requests.exceptions.Timeout, "Timeout Error"),
        (requests.exceptions.ConnectionError, "Connection Error"),
        (requests.exceptions.RequestException, "Request Error"),
        (ValueError, "Value Error"),
        (KeyError, "Key Error"),
    ],
)
def test_create_commit_handles_various_exceptions(
    sample_base_args, error_type, error_message
):
    """Test that various exception types are handled by the decorator."""
    with patch("services.github.commits.create_commit.requests.post") as mock_post:
        mock_post.side_effect = error_type(error_message)

        # The function should return None due to handle_exceptions decorator
        result = create_commit(sample_base_args, "Test message", "tree123", "parent456")
        assert result is None

        # Verify the request was attempted
        mock_post.assert_called_once()

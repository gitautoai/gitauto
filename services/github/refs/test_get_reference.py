import json
from unittest.mock import patch, MagicMock
import pytest
import requests
from config import TIMEOUT

from services.github.refs.get_reference import get_reference
from test_utils import create_test_base_args


@pytest.fixture
def base_args():
    """Fixture providing valid BaseArgs for testing."""
    return create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        new_branch="test-branch",
    )


@pytest.fixture
def mock_response():
    """Fixture providing a mock response object."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"object": {"sha": "abc123def456"}}
    return response


@pytest.fixture
def mock_404_response():
    """Fixture providing a mock 404 response."""
    response = MagicMock()
    response.status_code = 404
    return response


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch("services.github.refs.get_reference.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.refs.get_reference.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test-token"}
        yield mock


def test_get_reference_success(
    base_args, mock_response, mock_requests_get, mock_create_headers
):
    """Test successful reference retrieval."""
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    assert result == "abc123def456"
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test-token")


def test_get_reference_404_returns_none(
    base_args, mock_404_response, mock_requests_get, mock_create_headers
):
    """Test that 404 response returns None."""
    mock_requests_get.return_value = mock_404_response

    result = get_reference(base_args)

    assert result is None
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test-token")


def test_get_reference_constructs_correct_url(
    base_args, mock_response, mock_requests_get, mock_create_headers
):
    """Test that the correct GitHub API URL is constructed."""
    mock_requests_get.return_value = mock_response

    get_reference(base_args)

    expected_url = (
        "https://api.github.com/repos/test-owner/test-repo/git/ref/heads/test-branch"
    )
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test-token"},
        timeout=TIMEOUT,
    )


def test_get_reference_with_different_branch_names(
    mock_response, mock_requests_get, mock_create_headers
):
    """Test with various branch name formats."""
    test_cases = [
        "main",
        "feature/new-feature",
        "bugfix-123",
        "release/v1.0.0",
        "hotfix_urgent_fix",
    ]

    for branch_name in test_cases:
        mock_requests_get.reset_mock()
        mock_requests_get.return_value = mock_response

        args = create_test_base_args(
            owner="owner", repo="repo", token="token", new_branch=branch_name
        )

        result = get_reference(args)

        assert result == "abc123def456"
        expected_url = (
            f"https://api.github.com/repos/owner/repo/git/ref/heads/{branch_name}"
        )
        mock_requests_get.assert_called_with(
            url=expected_url,
            headers={"Authorization": "Bearer test-token"},
            timeout=TIMEOUT,
        )


def test_get_reference_with_special_characters_in_params(
    mock_response, mock_requests_get, mock_create_headers
):
    """Test with special characters in owner, repo, and branch names."""
    args = create_test_base_args(
        owner="test-owner-123",
        repo="test.repo_name",
        token="ghp_test123token",
        new_branch="feature/test-branch_v2",
    )
    mock_requests_get.return_value = mock_response

    result = get_reference(args)

    assert result == "abc123def456"
    expected_url = "https://api.github.com/repos/test-owner-123/test.repo_name/git/ref/heads/feature/test-branch_v2"
    mock_requests_get.assert_called_with(
        url=expected_url,
        headers={"Authorization": "Bearer test-token"},
        timeout=TIMEOUT,
    )


def test_get_reference_http_error_non_404(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of HTTP errors other than 404."""
    error_response = MagicMock()
    error_response.status_code = 403
    # Create a proper HTTPError with response object
    http_error = requests.exceptions.HTTPError("Forbidden")
    http_error.response = error_response
    error_response.reason = "Forbidden"
    error_response.text = "Access denied"
    # Add headers that handle_exceptions might expect for 403 errors
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
    }
    error_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = error_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator
    assert result is None


def test_get_reference_connection_error(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of connection errors."""
    mock_requests_get.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator
    assert result is None


def test_get_reference_timeout_error(base_args, mock_requests_get, mock_create_headers):
    """Test handling of timeout errors."""
    mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator
    assert result is None


def test_get_reference_json_decode_error(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of JSON decode errors."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator
    assert result is None


def test_get_reference_missing_object_key(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling when response JSON is missing 'object' key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ref": "refs/heads/main"}  # Missing 'object' key
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator catching KeyError
    assert result is None


def test_get_reference_missing_sha_key(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling when response JSON is missing 'sha' key in object."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "object": {"type": "commit"}
    }  # Missing 'sha' key
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator catching KeyError
    assert result is None


def test_get_reference_empty_response(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of empty response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator catching KeyError
    assert result is None


def test_get_reference_null_sha_value(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling when SHA value is null."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"object": {"sha": None}}
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    assert result is None  # cast(str, None) returns None


def test_get_reference_returns_string_sha(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that the function returns SHA as string."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"object": {"sha": "1234567890abcdef"}}
    mock_requests_get.return_value = mock_response

    result = get_reference(base_args)

    assert result == "1234567890abcdef"
    assert isinstance(result, str)


@pytest.mark.parametrize("status_code", [401, 403, 422, 500, 502, 503])
def test_get_reference_various_http_errors(
    base_args, mock_requests_get, mock_create_headers, status_code
):
    """Test handling of various HTTP error status codes."""
    error_response = MagicMock()
    error_response.status_code = status_code
    # Create a proper HTTPError with response object
    http_error = requests.exceptions.HTTPError(f"HTTP {status_code}")
    http_error.response = error_response
    error_response.reason = f"HTTP {status_code}"
    error_response.text = f"Error {status_code}"
    # Add headers that handle_exceptions might expect for certain status codes
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
    }
    error_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = error_response

    result = get_reference(base_args)

    # Should return None due to handle_exceptions decorator
    assert result is None


def test_get_reference_calls_raise_for_status_on_non_404(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that raise_for_status is called for non-404 responses."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"object": {"sha": "test-sha"}}
    mock_requests_get.return_value = mock_response

    get_reference(base_args)

    mock_response.raise_for_status.assert_called_once()

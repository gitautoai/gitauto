from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.comments.get_all_comments import get_all_comments
from tests.constants import OWNER, REPO, TOKEN
from tests.helpers.create_test_base_args import create_test_base_args


@pytest.fixture
def base_args():
    """Fixture providing base arguments for testing."""
    return {"owner": OWNER, "repo": REPO, "token": TOKEN, "issue_number": 123}


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get function."""
    with patch("services.github.comments.get_all_comments.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.comments.get_all_comments.create_headers") as mock:
        mock.return_value = {"Authorization": f"Bearer {TOKEN}"}
        yield mock


def test_get_all_comments_success(base_args, mock_requests_get, mock_create_headers):
    """Test successful retrieval of comments."""
    # Arrange
    expected_comments = [
        {"id": 1, "body": "First comment", "user": {"login": "user1"}},
        {"id": 2, "body": "Second comment", "user": {"login": "user2"}},
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = expected_comments
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert result == expected_comments
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_empty_response(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of empty comments list."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert result == []
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_correct_url_construction(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that the correct GitHub API URL is constructed."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/123/comments"
    mock_requests_get.assert_called_once()
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_correct_headers(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that correct headers are passed to the request."""
    # Arrange
    expected_headers = {"Authorization": f"Bearer {TOKEN}"}
    mock_create_headers.return_value = expected_headers
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN)
    call_args = mock_requests_get.call_args
    assert call_args[1]["headers"] == expected_headers


def test_get_all_comments_timeout_parameter(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that timeout parameter is correctly passed."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    call_args = mock_requests_get.call_args
    assert "timeout" in call_args[1]
    # Timeout should be imported from config
    from config import TIMEOUT

    assert call_args[1]["timeout"] == TIMEOUT


def test_get_all_comments_http_error(base_args, mock_requests_get, mock_create_headers):
    """Test handling of HTTP errors."""
    # Arrange
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Repository not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert (
        result == []
    )  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_all_comments_json_decode_error(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of JSON decode errors."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert (
        result == []
    )  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_network_error(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of network errors."""
    # Arrange
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert (
        result == []
    )  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()


def test_get_all_comments_different_issue_number(
    mock_requests_get, mock_create_headers
):
    """Test with different issue numbers."""
    # Arrange
    base_args = create_test_base_args(
        owner=OWNER, repo=REPO, token=TOKEN, issue_number=456
    )
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/456/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_different_owner_repo(mock_requests_get, mock_create_headers):
    """Test with different owner and repository."""
    # Arrange
    base_args = create_test_base_args(
        owner="different_owner",
        repo="different_repo",
        token=TOKEN,
        issue_number=123,
    )
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    expected_url = "https://api.github.com/repos/different_owner/different_repo/issues/123/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_large_response(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of large comment responses."""
    # Arrange
    large_comments = [
        {"id": i, "body": f"Comment {i}", "user": {"login": f"user{i}"}}
        for i in range(100)
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = large_comments
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert result == large_comments
    assert len(result) == 100
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # The function should have the handle_exceptions decorator applied
    assert hasattr(get_all_comments, "__wrapped__")


def test_get_all_comments_with_special_characters_in_repo_name(
    mock_requests_get, mock_create_headers
):
    """Test with repository names containing special characters."""
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo-with-dashes_and_underscores",
        "token": TOKEN,
        "issue_number": 123,
    }
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    expected_url = "https://api.github.com/repos/test-owner/test-repo-with-dashes_and_underscores/issues/123/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


@pytest.mark.parametrize("issue_number", [1, 999999, 123456789])
def test_get_all_comments_with_various_issue_numbers(
    mock_requests_get, mock_create_headers, issue_number
):
    """Test with various issue number formats."""
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
    }
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    expected_url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
    )
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


@pytest.mark.parametrize(
    "error_type,error_message",
    [
        (requests.exceptions.ConnectionError, "Connection failed"),
        (requests.exceptions.Timeout, "Request timed out"),
        (requests.exceptions.RequestException, "Request failed"),
        (ValueError, "Invalid value"),
        (KeyError, "Missing key"),
    ],
)
def test_get_all_comments_various_exceptions(
    base_args, mock_requests_get, mock_create_headers, error_type, error_message
):
    """Test handling of various exception types."""
    # Arrange
    mock_requests_get.side_effect = error_type(error_message)

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert (
        result == []
    )  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()


def test_get_all_comments_uses_github_api_url_constant(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that the function uses the GITHUB_API_URL constant."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    with patch(
        "services.github.comments.get_all_comments.GITHUB_API_URL",
        "https://custom.api.github.com",
    ):
        get_all_comments(base_args)

    # Assert
    expected_url = (
        f"https://custom.api.github.com/repos/{OWNER}/{REPO}/issues/123/comments"
    )
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_response_with_complex_comment_structure(
    base_args, mock_requests_get, mock_create_headers
):
    """Test handling of complex comment response structure."""
    # Arrange
    complex_comments = [
        {
            "id": 1,
            "url": "https://api.github.com/repos/owner/repo/issues/comments/1",
            "html_url": "https://github.com/owner/repo/issues/123#issuecomment-1",
            "body": "This is a test comment",
            "user": {
                "login": "test-user",
                "id": 12345,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
                "type": "User",
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "author_association": "OWNER",
            "reactions": {
                "total_count": 0,
                "+1": 0,
                "-1": 0,
                "laugh": 0,
                "hooray": 0,
                "confused": 0,
                "heart": 0,
                "rocket": 0,
                "eyes": 0,
            },
        }
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = complex_comments
    mock_requests_get.return_value = mock_response

    # Act
    result = get_all_comments(base_args)

    # Assert
    assert result == complex_comments
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["user"]["login"] == "test-user"
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_function_signature_compliance():
    """Test that the function signature matches expected parameters."""
    import inspect

    sig = inspect.signature(get_all_comments)
    params = list(sig.parameters.keys())

    # Verify parameter names and order
    expected_params = ["base_args"]
    assert params == expected_params

    # Verify parameter type annotation
    from services.github.types.github_types import BaseArgs

    assert sig.parameters["base_args"].annotation == BaseArgs

    # Verify return type annotation
    assert (
        sig.return_annotation == inspect.Signature.empty
    )  # No explicit return annotation


def test_get_all_comments_with_empty_token(mock_requests_get, mock_create_headers):
    """Test with empty token."""
    base_args = {"owner": OWNER, "repo": REPO, "token": "", "issue_number": 123}
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Act
    get_all_comments(base_args)

    # Assert
    mock_create_headers.assert_called_once_with(token="")
    mock_requests_get.assert_called_once()


def test_get_all_comments_multiple_calls_independence(
    base_args, mock_requests_get, mock_create_headers
):
    """Test that multiple calls to the function are independent."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1, "body": "test"}]
    mock_requests_get.return_value = mock_response

    # Act
    result1 = get_all_comments(base_args)
    result2 = get_all_comments(base_args)

    # Assert
    assert result1 == result2
    assert mock_requests_get.call_count == 2
    assert mock_create_headers.call_count == 2
    assert mock_response.json.call_count == 2

from unittest.mock import patch, MagicMock
import pytest
import requests
from requests import HTTPError
from services.github.comments.delete_comment import delete_comment
from test_utils import create_test_base_args


@pytest.fixture
def base_args():
    """Fixture providing test BaseArgs."""
    return create_test_base_args(
        owner="test-owner", repo="test-repo", token="test-token-123"
    )


@pytest.fixture
def mock_delete_response():
    """Fixture providing a mocked successful delete response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.comments.delete_comment.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token-123",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


def test_delete_comment_success(base_args, mock_delete_response, mock_create_headers):
    """Test successful comment deletion."""
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        result = delete_comment(base_args, comment_id)

        # Verify the delete request was made with correct parameters
        mock_delete.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/issues/comments/12345",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer test-token-123",
                "User-Agent": "GitAuto",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=120,
        )

        # Verify headers were created with correct token
        mock_create_headers.assert_called_once_with(token="test-token-123")

        # Verify response status was checked
        mock_delete_response.raise_for_status.assert_called_once()

        # Function should return None on success (due to handle_exceptions decorator)
        assert result is None


def test_delete_comment_with_different_comment_id(
    base_args, mock_delete_response, mock_create_headers
):
    """Test comment deletion with different comment ID."""
    comment_id = 98765

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(base_args, comment_id)

        # Verify URL contains the correct comment ID
        expected_url = (
            "https://api.github.com/repos/test-owner/test-repo/issues/comments/98765"
        )
        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert actual_call[1]["url"] == expected_url


def test_delete_comment_with_different_owner_repo(
    mock_delete_response, mock_create_headers
):
    """Test comment deletion with different owner and repo."""
    base_args = create_test_base_args(
        owner="different-owner", repo="different-repo", token="different-token"
    )
    comment_id = 54321

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(base_args, comment_id)

        # Verify URL contains correct owner and repo
        expected_url = "https://api.github.com/repos/different-owner/different-repo/issues/comments/54321"
        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert actual_call[1]["url"] == expected_url

        # Verify headers were created with correct token
        mock_create_headers.assert_called_once_with(token="different-token")


def test_delete_comment_http_error_handled(base_args, mock_create_headers):
    """Test that HTTP errors are handled by the decorator."""
    comment_id = 12345

    # Create a mock response with an HTTP error
    mock_response = MagicMock()
    # Create a proper HTTPError with a response object
    http_error = HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Comment not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_response

        # Should return None due to handle_exceptions decorator with raise_on_error=False
        result = delete_comment(base_args, comment_id)

        assert result is None
        mock_delete.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_delete_comment_request_timeout_handled(base_args, mock_create_headers):
    """Test that request timeout is handled by the decorator."""
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.side_effect = requests.exceptions.Timeout("Request timed out")

        # Should return None due to handle_exceptions decorator
        result = delete_comment(base_args, comment_id)

        assert result is None
        mock_delete.assert_called_once()


def test_delete_comment_uses_correct_timeout(
    base_args, mock_delete_response, mock_create_headers
):
    """Test that the function uses the correct timeout value."""
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        with patch("services.github.comments.delete_comment.TIMEOUT", 60):
            mock_delete.return_value = mock_delete_response

            delete_comment(base_args, comment_id)

            # Verify timeout parameter
            mock_delete.assert_called_once()
            actual_call = mock_delete.call_args
            assert actual_call[1]["timeout"] == 60


def test_delete_comment_uses_github_api_url(
    base_args, mock_delete_response, mock_create_headers
):
    """Test that the function uses the correct GitHub API URL."""
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        with patch(
            "services.github.comments.delete_comment.GITHUB_API_URL",
            "https://custom.api.github.com",
        ):
            mock_delete.return_value = mock_delete_response

            delete_comment(base_args, comment_id)

            # Verify URL uses the custom API URL
            expected_url = "https://custom.api.github.com/repos/test-owner/test-repo/issues/comments/12345"
            mock_delete.assert_called_once()
            actual_call = mock_delete.call_args
            assert actual_call[1]["url"] == expected_url


@pytest.mark.parametrize("comment_id", [1, 999999, 123456789])
def test_delete_comment_with_various_comment_ids(
    base_args, mock_delete_response, mock_create_headers, comment_id
):
    """Test comment deletion with various comment ID formats."""
    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(base_args, comment_id)

        # Verify URL contains the correct comment ID
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/issues/comments/{comment_id}"
        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert actual_call[1]["url"] == expected_url


def test_delete_comment_connection_error_handled(base_args, mock_create_headers):
    """Test that connection errors are handled by the decorator."""
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        # Should return None due to handle_exceptions decorator
        result = delete_comment(base_args, comment_id)

        assert result is None
        mock_delete.assert_called_once()


def test_delete_comment_with_special_characters_in_repo_name(
    mock_delete_response, mock_create_headers
):
    """Test comment deletion with special characters in repository name."""
    base_args = create_test_base_args(
        owner="test-owner", repo="test-repo-with-dashes", token="test-token"
    )
    comment_id = 12345

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(base_args, comment_id)

        # Verify URL handles special characters correctly
        expected_url = "https://api.github.com/repos/test-owner/test-repo-with-dashes/issues/comments/12345"
        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert actual_call[1]["url"] == expected_url


def test_delete_comment_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # Import the function to check its decorator
    from services.github.comments.delete_comment import delete_comment

    # The function should have the handle_exceptions decorator applied
    # We can verify this by checking if the function has been wrapped
    assert hasattr(delete_comment, "__wrapped__")

    # The decorator should be configured with default_return_value=None and raise_on_error=False
    # This is tested implicitly by the error handling tests above

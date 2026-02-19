# pylint: disable=unused-argument

from unittest.mock import patch, MagicMock
import pytest

from services.github.files.delete_remote_file import delete_remote_file


@pytest.fixture
def base_args(tmp_path):
    """Fixture for base arguments."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
        "clone_dir": str(tmp_path),
    }


@pytest.fixture
def mock_requests():
    """Fixture for mocking requests."""
    with patch("services.github.files.delete_remote_file.requests") as mock:
        mock.delete.return_value = MagicMock(status_code=200)
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture for mocking create_headers."""
    with patch("services.github.files.delete_remote_file.create_headers") as mock:
        mock.return_value = {"Authorization": "token test-token"}
        yield mock


def test_delete_file_successful(base_args, mock_requests, mock_create_headers):
    """Test successful file deletion."""
    file_path = "test/file.txt"
    sha = "abc123"

    result = delete_remote_file(file_path=file_path, sha=sha, base_args=base_args)

    assert result == f"File {file_path} successfully deleted"
    mock_requests.delete.assert_called_once()
    mock_create_headers.assert_called_once_with(token=base_args["token"])


def test_delete_file_with_custom_message(base_args, mock_requests, mock_create_headers):
    """Test file deletion with custom commit message."""
    file_path = "test/file.txt"
    sha = "abc123"
    custom_message = "Custom deletion message"

    delete_remote_file(
        file_path=file_path, sha=sha, base_args=base_args, commit_message=custom_message
    )

    called_args = mock_requests.delete.call_args[1]
    assert called_args["json"]["message"] == custom_message


def test_delete_file_with_skip_ci(base_args, mock_requests, mock_create_headers):
    """Test file deletion with skip_ci flag."""
    file_path = "test/file.txt"
    sha = "abc123"
    base_args["skip_ci"] = True

    delete_remote_file(file_path=file_path, sha=sha, base_args=base_args)

    called_args = mock_requests.delete.call_args[1]
    assert called_args["json"]["message"] == f"Delete {file_path} [skip ci]"


def test_delete_file_request_error(base_args, mock_requests, mock_create_headers):
    """Test file deletion with request error."""
    mock_requests.delete.side_effect = Exception("Network error")

    result = delete_remote_file(
        file_path="test/file.txt", sha="abc123", base_args=base_args
    )

    assert result is None  # Due to @handle_exceptions decorator


def test_delete_file_http_error(base_args, mock_requests, mock_create_headers):
    """Test file deletion with HTTP error."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP error")
    mock_requests.delete.return_value = mock_response

    result = delete_remote_file(
        file_path="test/file.txt", sha="abc123", base_args=base_args
    )

    assert result is None  # Due to @handle_exceptions decorator

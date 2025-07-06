# Standard imports
import base64
from unittest.mock import patch, MagicMock, call

# Third party imports
import pytest
import requests

# Local imports
from services.github.commits.apply_diff_to_file import apply_diff_to_file
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_requests_put():
    """Fixture to mock requests.put."""
    with patch("services.github.commits.apply_diff_to_file.requests.put") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers."""
    with patch("services.github.commits.apply_diff_to_file.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def mock_apply_patch():
    """Fixture to mock apply_patch."""
    with patch("services.github.commits.apply_diff_to_file.apply_patch") as mock:
        yield mock


@pytest.fixture
def base_args():
    """Fixture to provide base arguments."""
    return {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "new_branch": "test_branch",
    }


def test_apply_diff_to_file_success(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch, base_args):
    """Test successful application of diff to an existing file."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"original content").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    mock_response_put = MagicMock()
    mock_response_put.status_code = 200
    mock_requests_put.return_value = mock_response_put

    mock_apply_patch.return_value = ("modified content", "")

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="original content", diff_text="test diff"
    )
    mock_requests_put.assert_called_once()
    mock_response_put.raise_for_status.assert_called_once()
    assert "successfully" in result


def test_apply_diff_to_file_new_file(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch, base_args):
    """Test creating a new file with diff."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 404
    mock_requests_get.return_value = mock_response_get

    mock_response_put = MagicMock()
    mock_response_put.status_code = 200
    mock_requests_put.return_value = mock_response_put

    mock_apply_patch.return_value = ("new file content", "")

    # Execute
    result = apply_diff_to_file(
        diff="test diff for new file",
        file_path="new_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="", diff_text="test diff for new file"
    )
    mock_requests_put.assert_called_once()
    mock_response_put.raise_for_status.assert_called_once()
    assert "successfully" in result


def test_apply_diff_to_file_delete_file(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch, base_args):
    """Test deleting a file with diff."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"content to delete").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    mock_response_put = MagicMock()
    mock_response_put.status_code = 200
    mock_requests_put.return_value = mock_response_put

    # Return empty modified_text to simulate file deletion
    mock_apply_patch.return_value = ("", "")

    # Execute
    result = apply_diff_to_file(
        diff="test diff for deletion",
        file_path="file_to_delete.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="content to delete", diff_text="test diff for deletion"
    )
    
    # Verify the data for deletion has the correct format
    expected_data = {
        "message": "Delete file_to_delete.py",
        "branch": "test_branch",
        "sha": "test_sha",
    }
    mock_requests_put.assert_called_once()
    call_args = mock_requests_put.call_args[1]
    assert call_args["json"] == expected_data
    
    mock_response_put.raise_for_status.assert_called_once()
    assert "successfully" in result


def test_apply_diff_to_file_skip_ci(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch):
    """Test applying diff with skip_ci flag."""
    # Setup
    base_args = {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "new_branch": "test_branch",
        "skip_ci": True,
    }

    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"original content").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    mock_response_put = MagicMock()
    mock_response_put.status_code = 200
    mock_requests_put.return_value = mock_response_put

    mock_apply_patch.return_value = ("modified content", "")

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="original content", diff_text="test diff"
    )
    
    # Verify the commit message includes [skip ci]
    call_args = mock_requests_put.call_args[1]
    assert call_args["json"]["message"] == "Update test_file.py [skip ci]"
    
    mock_response_put.raise_for_status.assert_called_once()
    assert "successfully" in result


def test_apply_diff_to_file_directory_error(mock_requests_get, mock_create_headers, base_args):
    """Test error when file_path is a directory."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "type": "dir",
    }
    mock_requests_get.return_value = mock_response_get

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_directory/",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    assert "is a directory" in result


def test_apply_diff_to_file_multiple_files_error(mock_requests_get, mock_create_headers, base_args):
    """Test error when file_path returns multiple files."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = [
        {"name": "file1.py", "path": "test_directory/file1.py"},
        {"name": "file2.py", "path": "test_directory/file2.py"},
    ]
    mock_requests_get.return_value = mock_response_get

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_directory",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    assert "multiple files" in result


def test_apply_diff_to_file_incorrect_diff_format(mock_requests_get, mock_create_headers, mock_apply_patch, base_args):
    """Test error when diff format is incorrect."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"original content").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    # Return empty modified_text but not for deletion (has rej_text)
    mock_apply_patch.return_value = ("", "Some rejection message")

    # Execute
    result = apply_diff_to_file(
        diff="invalid diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="original content", diff_text="invalid diff"
    )
    assert "diff format is incorrect" in result


def test_apply_diff_to_file_partial_application(mock_requests_get, mock_create_headers, mock_apply_patch, base_args):
    """Test when diff is partially applied with rejections."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"original content").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    # Return modified_text but with rejection text
    mock_apply_patch.return_value = ("partially modified", "rejection details")

    # Execute
    result = apply_diff_to_file(
        diff="partial diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    mock_apply_patch.assert_called_once_with(
        original_text="original content", diff_text="partial diff"
    )
    assert "partially applied" in result
    assert "rejected" in result


def test_apply_diff_to_file_missing_branch(base_args):
    """Test error when new_branch is not set."""
    # Setup
    base_args_without_branch = {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "new_branch": "",  # Empty branch name
    }

    # Execute and verify
    with pytest.raises(ValueError, match="new_branch is not set"):
        apply_diff_to_file(
            diff="test diff",
            file_path="test_file.py",
            base_args=base_args_without_branch,
        )


def test_apply_diff_to_file_http_error(mock_requests_get, mock_create_headers, base_args):
    """Test handling of HTTP errors."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
    mock_requests_get.return_value = mock_response_get

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    mock_requests_get.assert_called_once()
    mock_response_get.raise_for_status.assert_called_once()
    assert result is False  # Default return value from handle_exceptions


def test_apply_diff_to_file_with_kwargs(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch, base_args):
    """Test that extra kwargs are properly handled."""
    # This test ensures the **_kwargs parameter works correctly
    apply_diff_to_file(diff="test diff", file_path="test_file.py", base_args=base_args, extra_param="ignored")
    # If no exception is raised, the test passes


def test_apply_diff_to_file_put_error(mock_requests_get, mock_requests_put, mock_create_headers, mock_apply_patch, base_args):
    """Test handling of HTTP errors during PUT request."""
    # Setup
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {
        "content": base64.b64encode(b"original content").decode("utf-8"),
        "sha": "test_sha",
    }
    mock_requests_get.return_value = mock_response_get

    mock_response_put = MagicMock()
    mock_response_put.raise_for_status.side_effect = requests.exceptions.HTTPError("PUT Error")
    mock_requests_put.return_value = mock_response_put

    mock_apply_patch.return_value = ("modified content", "")

    # Execute
    result = apply_diff_to_file(
        diff="test diff",
        file_path="test_file.py",
        base_args=base_args,
    )

    # Verify
    assert result is False  # Default return value from handle_exceptions

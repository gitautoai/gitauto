# pylint: disable=unused-argument
import base64
from unittest.mock import MagicMock, patch
from typing import cast

import pytest
import requests

from services.github.commits.replace_remote_file import (
    REPLACE_REMOTE_FILE_CONTENT,
    replace_remote_file_content,
)
from services.github.types.github_types import BaseArgs


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs for testing."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
        "skip_ci": False,
    }


@pytest.fixture
def sample_base_args_with_skip_ci():
    """Fixture providing sample BaseArgs with skip_ci enabled."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
        "skip_ci": True,
    }


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch(
        "services.github.commits.replace_remote_file.create_headers"
    ) as mock_headers:
        mock_headers.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock_headers


@pytest.fixture
def mock_requests_get_existing_file():
    """Fixture to mock requests.get for existing file."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "file",
            "sha": "existing-file-sha",
            "content": base64.b64encode("existing content".encode("utf-8")).decode(
                "utf-8"
            ),
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_requests_get_nonexistent_file():
    """Fixture to mock requests.get for non-existent file."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_requests_put_success():
    """Fixture to mock successful requests.put."""
    with patch("services.github.commits.replace_remote_file.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        yield mock_put


def test_replace_existing_file_success(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test successful replacement of existing file content."""
    file_path = "src/test.py"
    file_content = "print('Hello, World!')"

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify GET request was made to check existing file
    expected_get_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
    mock_requests_get_existing_file.assert_called_once_with(
        url=expected_get_url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )

    # Verify PUT request was made with correct data
    # The implementation processes the content through ensure_final_newline
    processed_content = file_content + '\n' if not file_content.endswith('\n') else file_content
    expected_content = base64.b64encode(processed_content.encode("utf-8")).decode("utf-8")
    expected_data = {
        "message": f"Replace content of {file_path}",
        "content": expected_content,
        "branch": "test-branch",
        "sha": "existing-file-sha",
    }
    mock_requests_put_success.assert_called_once_with(
        url=expected_get_url,
        json=expected_data,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )

    # Verify create_headers was called
    mock_create_headers.assert_called_with(token="test-token")


def test_replace_nonexistent_file_success(
    mock_requests_get_nonexistent_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test successful creation of new file when file doesn't exist."""
    file_path = "src/new_file.py"
    file_content = "print('New file content')"

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify GET request was made
    expected_get_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
    mock_requests_get_nonexistent_file.assert_called_once_with(
        url=expected_get_url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )

    # Verify PUT request was made without SHA (new file)
    # The implementation processes the content through ensure_final_newline
    processed_content = file_content + '\n' if not file_content.endswith('\n') else file_content
    expected_content = base64.b64encode(processed_content.encode("utf-8")).decode("utf-8")
    expected_data = {
        "message": f"Replace content of {file_path}",
        "content": expected_content,
        "branch": "test-branch",
    }
    mock_requests_put_success.assert_called_once_with(
        url=expected_get_url,
        json=expected_data,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )


def test_replace_file_with_skip_ci(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args_with_skip_ci,
):
    """Test file replacement with skip_ci enabled."""
    file_path = "src/test.py"
    file_content = "print('Hello with skip CI')"

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args_with_skip_ci,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify PUT request includes [skip ci] in message
    call_args = mock_requests_put_success.call_args
    assert (
        call_args.kwargs["json"]["message"]
        == f"Replace content of {file_path} [skip ci]"
    )


def test_replace_file_directory_error(
    mock_create_headers,
    sample_base_args,
):
    """Test error when file_path points to a directory."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "dir",
            "sha": "directory-sha",
        }
        mock_get.return_value = mock_response

        file_path = "src/directory"
        file_content = "content"

        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=sample_base_args,
        )

        # Verify error message
        assert (
            result
            == f"file_path: '{file_path}' is a directory. It should be a file path."
        )


def test_replace_file_multiple_files_error(
    mock_create_headers,
    sample_base_args,
):
    """Test error when file_path returns multiple files."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"type": "file", "name": "file1.py"},
            {"type": "file", "name": "file2.py"},
        ]
        mock_get.return_value = mock_response

        file_path = "src/*"
        file_content = "content"

        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=sample_base_args,
        )

        # Verify error message
        assert (
            result
            == f"file_path: '{file_path}' returned multiple files. Please specify a single file path."
        )


def test_replace_file_with_special_characters(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test file replacement with special characters in content."""
    file_path = "src/unicode_test.py"
    file_content = "print('Hello 世界! 🌍 émojis and special chars: !@#$%^&*()')"

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify content was properly encoded
    call_args = mock_requests_put_success.call_args
    # The implementation processes the content through ensure_final_newline
    processed_content = file_content + '\n' if not file_content.endswith('\n') else file_content
    expected_content = base64.b64encode(processed_content.encode("utf-8")).decode("utf-8")
    assert call_args.kwargs["json"]["content"] == expected_content


def test_replace_file_with_empty_content(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test file replacement with empty content."""
    file_path = "src/empty.py"
    file_content = ""

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify empty content was properly encoded
    call_args = mock_requests_put_success.call_args
    expected_content = base64.b64encode("".encode("utf-8")).decode("utf-8")
    assert call_args.kwargs["json"]["content"] == expected_content


def test_replace_file_with_large_content(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test file replacement with large content."""
    file_path = "src/large_file.py"
    file_content = "# Large file content\n" * 1000

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify large content was properly encoded
    call_args = mock_requests_put_success.call_args
    expected_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
    assert call_args.kwargs["json"]["content"] == expected_content


def test_replace_file_get_request_error_handled(sample_base_args):
    """Test that GET request errors are handled by the decorator."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        http_error = requests.exceptions.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None


def test_replace_file_put_request_error_handled(
    mock_requests_get_existing_file,
    sample_base_args,
):
    """Test that PUT request errors are handled by the decorator."""
    with patch("services.github.commits.replace_remote_file.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.reason = "Unprocessable Entity"
        http_error = requests.exceptions.HTTPError("422 Unprocessable Entity")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_put.return_value = mock_response

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None


def test_replace_file_connection_error_handled(sample_base_args):
    """Test that connection errors are handled by the decorator."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None


def test_replace_file_timeout_error_handled(sample_base_args):
    """Test that timeout errors are handled by the decorator."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None


def test_replace_file_uses_correct_timeout(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    sample_base_args,
):
    """Test that correct timeout value is used for requests."""
    replace_remote_file_content(
        file_content="content",
        file_path="test.py",
        base_args=sample_base_args,
    )

    # Verify GET request uses correct timeout
    get_call_args = mock_requests_get_existing_file.call_args
    assert get_call_args.kwargs["timeout"] == 120

    # Verify PUT request uses correct timeout
    put_call_args = mock_requests_put_success.call_args
    assert put_call_args.kwargs["timeout"] == 120


def test_replace_file_with_different_base_args(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
):
    """Test file replacement with different BaseArgs values."""
    base_args = {
        "owner": "different-owner",
        "repo": "different-repo",
        "token": "different-token",
        "new_branch": "feature-branch",
        "skip_ci": False,
    }

    result = replace_remote_file_content(
        file_content="content",
        file_path="different/path.py",
        base_args=cast(BaseArgs, base_args),
    )

    # Verify the result
    assert result == "Content replaced in the file: different/path.py successfully."

    # Verify correct URL was constructed
    get_call_args = mock_requests_get_existing_file.call_args
    expected_url = "https://api.github.com/repos/different-owner/different-repo/contents/different/path.py?ref=feature-branch"
    assert get_call_args.kwargs["url"] == expected_url

    # Verify create_headers was called with correct token
    mock_create_headers.assert_called_with(token="different-token")


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
def test_replace_file_handles_various_exceptions(
    sample_base_args, error_type, error_message
):
    """Test that various exception types are handled by the decorator."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_get.side_effect = error_type(error_message)

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None
        mock_get.assert_called_once()


def test_replace_file_missing_sha_in_existing_file(
    mock_create_headers,
    sample_base_args,
):
    """Test handling when existing file response doesn't contain SHA."""
    with patch(
        "services.github.commits.replace_remote_file.requests.get"
    ) as mock_get, patch(
        "services.github.commits.replace_remote_file.requests.put"
    ) as mock_put:
        # Mock GET response without SHA
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {
            "type": "file",
            # Missing "sha" key
            "content": base64.b64encode("existing content".encode("utf-8")).decode(
                "utf-8"
            ),
        }
        mock_get.return_value = mock_get_response

        # Mock PUT response
        mock_put_response = MagicMock()
        mock_put_response.raise_for_status.return_value = None
        mock_put.return_value = mock_put_response

        result = replace_remote_file_content(
            file_content="new content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Should still succeed with empty SHA
        assert result == "Content replaced in the file: test.py successfully."

        # Verify PUT request includes empty SHA
        call_args = mock_put.call_args
        assert call_args.kwargs["json"]["sha"] == ""


def test_replace_file_with_nested_file_path(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test file replacement with nested file path."""
    file_path = "src/utils/helpers/deep/nested/file.py"
    file_content = "# Deeply nested file content"

    result = replace_remote_file_content(
        file_content=file_content,
        file_path=file_path,
        base_args=sample_base_args,
    )

    # Verify the result
    assert result == f"Content replaced in the file: {file_path} successfully."

    # Verify correct URL construction with nested path
    get_call_args = mock_requests_get_existing_file.call_args
    expected_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
    assert get_call_args.kwargs["url"] == expected_url


def test_replace_file_json_decode_error_on_get(sample_base_args):
    """Test handling of JSON decode error during GET request."""
    with patch("services.github.commits.replace_remote_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON response")
        mock_get.return_value = mock_response

        result = replace_remote_file_content(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
        )

        # Function should return None due to handle_exceptions decorator
        assert result is None


def test_replace_remote_file_content_function_definition():
    """Test that the REPLACE_REMOTE_FILE_CONTENT function definition is properly structured."""

    # Verify function definition structure
    assert REPLACE_REMOTE_FILE_CONTENT["name"] == "replace_remote_file_content"
    assert "description" in REPLACE_REMOTE_FILE_CONTENT
    assert "parameters" in REPLACE_REMOTE_FILE_CONTENT
    assert REPLACE_REMOTE_FILE_CONTENT.get("strict") is True

    # Verify parameters structure
    params = REPLACE_REMOTE_FILE_CONTENT["parameters"]
    if isinstance(params, dict):
        assert params.get("type") == "object"
        properties = params.get("properties", {})
        if isinstance(properties, dict):
            assert "file_path" in properties
            assert "file_content" in properties
        assert params.get("required") == ["file_path", "file_content"]
        assert params.get("additionalProperties") is False

        # Verify file_content parameter
        if isinstance(properties, dict) and "file_content" in properties:
            file_content_param = properties["file_content"]
            if isinstance(file_content_param, dict):
                assert file_content_param.get("type") == "string"
                assert "description" in file_content_param


def test_replace_file_with_extra_kwargs(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_create_headers,
    sample_base_args,
):
    """Test that function handles extra kwargs properly (they should be ignored)."""
    result = replace_remote_file_content(
        file_content="content",
        file_path="test.py",
        base_args=sample_base_args,
        extra_param="should_be_ignored",
        another_param=123,
    )

    # Should work normally despite extra parameters
    assert result == "Content replaced in the file: test.py successfully."

# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import base64
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
import requests

from services.claude.tools.file_modify_result import FileWriteResult
from services.github.commits.apply_diff_to_file import apply_diff_to_file
from services.github.types.github_types import BaseArgs


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs for testing."""
    return cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "test_branch",
            "skip_ci": False,
        },
    )


@pytest.fixture
def sample_base_args_with_skip_ci():
    """Fixture providing sample BaseArgs with skip_ci enabled."""
    return cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "test_branch",
            "skip_ci": True,
        },
    )


@pytest.fixture
def mock_requests_get_existing_file():
    """Fixture to mock requests.get for existing file."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        # Base64 encoded "print('hello world')\n"
        mock_response.json.return_value = {
            "content": "cHJpbnQoJ2hlbGxvIHdvcmxkJykK",
            "sha": "test_sha_123",
            "type": "file",
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_requests_get_404():
    """Fixture to mock requests.get for non-existing file (404)."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_requests_put_success():
    """Fixture to mock successful requests.put."""
    with patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        yield mock_put


@pytest.fixture
def mock_apply_patch_success():
    """Fixture to mock successful apply_patch."""
    with patch("services.github.commits.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = ("print('hello modified world')\n", "")
        yield mock_patch


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch(
        "services.github.commits.apply_diff_to_file.create_headers"
    ) as mock_headers:
        mock_headers.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock_headers


def test_successful_file_update(
    sample_base_args,
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test successful file update with existing file."""
    diff = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print('hello world')
+print('hello modified world')"""

    result = apply_diff_to_file(
        diff=diff, file_path="test.py", base_args=sample_base_args
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert result.file_path == "test.py"
    assert "Applied diff to test.py" in result.message
    assert result.content == "print('hello modified world')\n"

    # Verify GET request was made
    mock_requests_get_existing_file.assert_called_once()
    call_args = mock_requests_get_existing_file.call_args
    assert "test_owner/test_repo/contents/test.py" in call_args.kwargs["url"]
    assert "ref=test_branch" in call_args.kwargs["url"]

    # Verify PUT request was made
    mock_requests_put_success.assert_called_once()
    put_call_args = mock_requests_put_success.call_args
    assert put_call_args.kwargs["json"]["message"] == "Update test.py"
    assert put_call_args.kwargs["json"]["branch"] == "test_branch"
    assert put_call_args.kwargs["json"]["sha"] == "test_sha_123"
    assert "content" in put_call_args.kwargs["json"]


def test_successful_file_update_with_skip_ci(
    sample_base_args_with_skip_ci,
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test successful file update with skip_ci enabled."""
    diff = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print('hello world')
+print('hello modified world')"""

    result = apply_diff_to_file(
        diff=diff, file_path="test.py", base_args=sample_base_args_with_skip_ci
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Applied diff to test.py" in result.message

    # Verify PUT request has [skip ci] in message
    mock_requests_put_success.assert_called_once()
    put_call_args = mock_requests_put_success.call_args
    assert put_call_args.kwargs["json"]["message"] == "Update test.py [skip ci]"


def test_new_file_creation(
    sample_base_args,
    mock_requests_get_404,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test creating a new file when it doesn't exist (404)."""
    diff = """--- /dev/null
+++ new_file.py
@@ -0,0 +1,1 @@
+print('new file content')"""

    result = apply_diff_to_file(
        diff=diff, file_path="new_file.py", base_args=sample_base_args
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert result.file_path == "new_file.py"
    assert "Applied diff to new_file.py" in result.message

    # Verify GET request returned 404
    mock_requests_get_404.assert_called_once()

    # Verify PUT request was made without SHA (new file)
    mock_requests_put_success.assert_called_once()
    put_call_args = mock_requests_put_success.call_args
    assert "sha" not in put_call_args.kwargs["json"]
    assert put_call_args.kwargs["json"]["message"] == "Update new_file.py"
    assert put_call_args.kwargs["json"]["branch"] == "test_branch"


def test_deletion_diff_rejected(mock_requests_get_existing_file):
    """Test that deletion diffs are rejected with proper error message."""
    base_args = cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "test_branch",
        },
    )

    deletion_diff = """--- utils/files/test_file.py
+++ /dev/null
@@ -1 +0,0 @@
-# Temporary file to check existing content"""

    result = apply_diff_to_file(
        diff=deletion_diff, file_path="utils/files/test_file.py", base_args=base_args
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "Cannot delete files" in result.message
    assert "delete_file" in result.message


def test_missing_new_branch_error():
    """Test that missing new_branch returns FileWriteResult due to handle_exceptions."""
    base_args = cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": None,
        },
    )

    result = apply_diff_to_file(
        diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert result.file_path == "test.py"


def test_empty_new_branch_error():
    """Test that empty new_branch returns FileWriteResult due to handle_exceptions."""
    base_args = cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "",
        },
    )

    result = apply_diff_to_file(
        diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert result.file_path == "test.py"


def test_directory_path_error(mock_create_headers):
    """Test error when file_path points to a directory."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "dir",
            "name": "test_directory",
        }
        mock_get.return_value = mock_response

        base_args = cast(
            BaseArgs,
            {
                "owner": "test_owner",
                "repo": "test_repo",
                "token": "test_token",
                "new_branch": "test_branch",
            },
        )

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test_directory",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "directory" in result.message


def test_multiple_files_error(mock_create_headers):
    """Test error when file_path returns multiple files (list response)."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"name": "file1.py", "type": "file"},
            {"name": "file2.py", "type": "file"},
        ]
        mock_get.return_value = mock_response

        base_args = cast(
            BaseArgs,
            {
                "owner": "test_owner",
                "repo": "test_repo",
                "token": "test_token",
                "new_branch": "test_branch",
            },
        )

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="ambiguous_path",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "multiple files" in result.message


def test_incorrect_diff_format(
    sample_base_args,
    mock_requests_get_existing_file,
    mock_create_headers,
):
    """Test handling of incorrect diff format."""
    with patch("services.github.commits.apply_diff_to_file.apply_patch") as mock_patch:
        # apply_patch returns empty string for incorrect diff
        mock_patch.return_value = ("", "")

        diff = "invalid diff format"

        result = apply_diff_to_file(
            diff=diff, file_path="test.py", base_args=sample_base_args
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "Invalid diff format" in result.message
        assert "diff=" in result.message


def test_partially_applied_diff(
    sample_base_args,
    mock_requests_get_existing_file,
    mock_create_headers,
):
    """Test handling of partially applied diff with rejections."""
    with patch("services.github.commits.apply_diff_to_file.apply_patch") as mock_patch:
        # apply_patch returns modified text but also rejection text
        mock_patch.return_value = ("partially modified content", "rejected changes")

        diff = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print('hello world')
+print('hello modified world')"""

        result = apply_diff_to_file(
            diff=diff, file_path="test.py", base_args=sample_base_args
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "partially applied" in result.message
        assert "rejected" in result.message
        assert "diff=" in result.message
        assert "rej_text=" in result.message


def test_http_error_on_get_request(sample_base_args, mock_create_headers):
    """Test handling of HTTP error during GET request."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "403 Forbidden"
        )
        mock_get.return_value = mock_response

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert result.file_path == "test.py"


def test_http_error_on_put_request(
    sample_base_args,
    mock_requests_get_existing_file,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test handling of HTTP error during PUT request."""
    with patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "422 Unprocessable Entity"
        )
        mock_put.return_value = mock_response

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert result.file_path == "test.py"


def test_base64_decoding_with_special_characters(
    sample_base_args,
    mock_requests_put_success,
    mock_create_headers,
):
    """Test base64 decoding with special characters and unicode."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        # Base64 encoded content with special characters: "print('héllo wörld 🌍')\n"
        special_content = "print('héllo wörld 🌍')\n"
        encoded_content = base64.b64encode(special_content.encode("utf-8")).decode(
            "utf-8"
        )
        mock_response.json.return_value = {
            "content": encoded_content,
            "sha": "test_sha_special",
            "type": "file",
        }
        mock_get.return_value = mock_response

        with patch(
            "services.github.commits.apply_diff_to_file.apply_patch"
        ) as mock_patch:
            mock_patch.return_value = ("print('héllo modified wörld 🌍')\n", "")

            diff = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print('héllo wörld 🌍')
+print('héllo modified wörld 🌍')"""

            result = apply_diff_to_file(
                diff=diff, file_path="test.py", base_args=sample_base_args
            )

            assert isinstance(result, FileWriteResult)
            assert result.success is True
            assert "Applied diff to test.py" in result.message

            # Verify apply_patch was called with decoded content
            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            assert call_args[1]["original_text"] == special_content


def test_missing_content_field_in_response(
    sample_base_args,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test handling when content field is missing from API response."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "sha": "test_sha_no_content",
            "type": "file",
            # Missing "content" field
        }
        mock_get.return_value = mock_response

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert "Applied diff to test.py" in result.message


def test_missing_sha_field_in_response(
    sample_base_args,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test handling when sha field is missing from API response."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": "cHJpbnQoJ2hlbGxvIHdvcmxkJykK",
            "type": "file",
            # Missing "sha" field
        }
        mock_get.return_value = mock_response

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert "Applied diff to test.py" in result.message

        # Verify PUT request was made without SHA
        mock_requests_put_success.assert_called_once()
        put_call_args = mock_requests_put_success.call_args
        assert "sha" not in put_call_args.kwargs["json"]


def test_url_construction_with_special_characters(
    mock_requests_get_existing_file,
    mock_requests_put_success,
    mock_apply_patch_success,
    mock_create_headers,
):
    """Test URL construction with special characters in owner, repo, and file path."""
    base_args = cast(
        BaseArgs,
        {
            "owner": "test-owner_123",
            "repo": "test.repo-name_456",
            "token": "test_token",
            "new_branch": "feature/test-branch_789",
        },
    )

    file_path = "src/utils/test_file-name_123.py"

    result = apply_diff_to_file(
        diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
        file_path=file_path,
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert result.file_path == "src/utils/test_file-name_123.py"
    assert "Applied diff to src/utils/test_file-name_123.py" in result.message

    # Verify GET request URL construction
    mock_requests_get_existing_file.assert_called_once()
    get_call_args = mock_requests_get_existing_file.call_args
    expected_url_parts = [
        "test-owner_123",
        "test.repo-name_456",
        "src/utils/test_file-name_123.py",
        "ref=feature/test-branch_789",
    ]
    for part in expected_url_parts:
        assert part in get_call_args.kwargs["url"]


def test_base64_encoding_in_put_request(
    sample_base_args,
    mock_requests_get_existing_file,
    mock_create_headers,
):
    """Test that content is properly base64 encoded in PUT request."""
    with patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        with patch(
            "services.github.commits.apply_diff_to_file.apply_patch"
        ) as mock_patch:
            modified_content = "print('modified content with special chars: éñ 🚀')\n"
            mock_patch.return_value = (modified_content, "")

            result = apply_diff_to_file(
                diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
                file_path="test.py",
                base_args=sample_base_args,
            )

            assert isinstance(result, FileWriteResult)
            assert result.success is True
            assert "Applied diff to test.py" in result.message

            # Verify PUT request content is base64 encoded
            mock_put.assert_called_once()
            put_call_args = mock_put.call_args
            encoded_content = put_call_args.kwargs["json"]["content"]

            # Decode and verify it matches the modified content
            decoded_content = base64.b64decode(encoded_content).decode("utf-8")
            assert decoded_content == modified_content


def test_kwargs_parameter_ignored():
    """Test that additional kwargs are ignored."""
    base_args = cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "test_branch",
        },
    )

    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with patch(
            "services.github.commits.apply_diff_to_file.requests.put"
        ) as mock_put:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_put.return_value = mock_response

            with patch(
                "services.github.commits.apply_diff_to_file.apply_patch"
            ) as mock_patch:
                mock_patch.return_value = ("new content", "")

                # Call with additional kwargs that should be ignored
                result = apply_diff_to_file(
                    diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
                    file_path="test.py",
                    base_args=base_args,
                    extra_param="should_be_ignored",
                    another_param=123,
                )

                assert isinstance(result, FileWriteResult)
                assert result.success is True
                assert "Applied diff to test.py" in result.message


@pytest.mark.parametrize(
    "error_type,error_message",
    [
        (requests.exceptions.Timeout, "Request timed out"),
        (requests.exceptions.ConnectionError, "Connection failed"),
        (requests.exceptions.RequestException, "Request failed"),
        (ValueError, "Value error occurred"),
        (KeyError, "Key error occurred"),
    ],
)
def test_various_exceptions_handled(sample_base_args, error_type, error_message):
    """Test that various exception types are handled by the decorator."""
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get:
        mock_get.side_effect = error_type(error_message)

        result = apply_diff_to_file(
            diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert result.file_path == "test.py"
        mock_get.assert_called_once()

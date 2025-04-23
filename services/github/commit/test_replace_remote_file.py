import base64
import unittest
from unittest.mock import patch, MagicMock

import requests

from config import GITHUB_API_URL, UTF8
from services.github.commit.replace_remote_file import replace_remote_file_content
from services.github.github_types import BaseArgs
from tests.constants import OWNER, REPO, TOKEN


def test_replace_remote_file_content_success():
    file_path = "test/file.py"
    file_content = "def test_function():\n    return True"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 200
    get_mock.json.return_value = {
        "type": "file",
        "sha": "abc123",
        "content": base64.b64encode("old content".encode(UTF8)).decode(UTF8)
    }

    put_mock = MagicMock()
    put_mock.status_code = 200

    with patch('requests.get', return_value=get_mock) as mock_get, \
         patch('requests.put', return_value=put_mock) as mock_put:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        assert result == f"Content replaced in the file: {file_path} successfully."
        expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/contents/{file_path}?ref=test-branch"
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["url"] == expected_url

        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        assert kwargs["url"] == expected_url
        expected_content = base64.b64encode(file_content.encode(UTF8)).decode(UTF8)
        assert kwargs["json"]["content"] == expected_content
        assert kwargs["json"]["sha"] == "abc123"
        assert kwargs["json"]["branch"] == "test-branch"
        assert kwargs["json"]["message"] == f"Replace content of {file_path}"


def test_replace_remote_file_content_new_file():
    file_path = "new/file.py"
    file_content = "def new_function():\n    return True"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 404

    put_mock = MagicMock()
    put_mock.status_code = 201

    with patch('requests.get', return_value=get_mock) as mock_get, \
         patch('requests.put', return_value=put_mock) as mock_put:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        assert result == f"Content replaced in the file: {file_path} successfully."
        expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/contents/{file_path}?ref=test-branch"
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        expected_content = base64.b64encode(file_content.encode(UTF8)).decode(UTF8)
        assert kwargs["json"]["content"] == expected_content
        assert "sha" not in kwargs["json"]
        assert kwargs["json"]["branch"] == "test-branch"


def test_replace_remote_file_content_directory_error():
    file_path = "some/directory/"
    file_content = "content"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 200
    get_mock.json.return_value = {
        "type": "dir",
        "sha": "dir123"
    }

    with patch('requests.get', return_value=get_mock) as mock_get:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        assert result == f"file_path: '{file_path}' is a directory. It should be a file path."
        mock_get.assert_called_once()


def test_replace_remote_file_content_multiple_files_error():
    file_path = "some/pattern*"
    file_content = "content"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 200
    get_mock.json.return_value = [
        {"name": "file1.py", "type": "file"},
        {"name": "file2.py", "type": "file"}
    ]

    with patch('requests.get', return_value=get_mock) as mock_get:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        expected = f"file_path: '{file_path}' returned multiple files. Please specify a single file path."
        assert result == expected
        mock_get.assert_called_once()


def test_replace_remote_file_content_get_request_error():
    file_path = "test/file.py"
    file_content = "content"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 500
    get_mock.raise_for_status.side_effect = requests.HTTPError("Server error")

    with patch('requests.get', return_value=get_mock) as mock_get:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        assert result is None
        mock_get.assert_called_once()


def test_replace_remote_file_content_put_request_error():
    file_path = "test/file.py"
    file_content = "content"
    base_args = BaseArgs(owner=OWNER, repo=REPO, token=TOKEN, new_branch="test-branch")

    get_mock = MagicMock()
    get_mock.status_code = 200
    get_mock.json.return_value = {
        "type": "file",
        "sha": "abc123"
    }

    put_mock = MagicMock()
    put_mock.raise_for_status.side_effect = requests.HTTPError("Server error")

    with patch('requests.get', return_value=get_mock) as mock_get, \
         patch('requests.put', return_value=put_mock) as mock_put:
        result = replace_remote_file_content(
            file_content=file_content,
            file_path=file_path,
            base_args=base_args
        )
        assert result is None
        mock_get.assert_called_once()
        mock_put.assert_called_once()


if __name__ == "__main__":
    unittest.main()

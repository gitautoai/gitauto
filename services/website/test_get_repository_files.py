# pylint: disable=unused-argument
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from services.website.get_repository_files import RepositoryFile, get_repository_files


@pytest.fixture
def mock_verify_api_key():
    with patch("services.website.get_repository_files.verify_api_key") as mock:
        yield mock


@pytest.fixture
def mock_get_file_tree():
    with patch("services.website.get_repository_files.get_file_tree") as mock:
        yield mock


def test_get_repository_files_success(mock_verify_api_key, mock_get_file_tree):
    mock_get_file_tree.return_value = [
        {"path": "src/main.py", "sha": "abc123", "size": 100, "type": "blob"},
        {"path": "src/utils.py", "sha": "def456", "size": 200, "type": "blob"},
    ]

    result = get_repository_files(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        token="test-token",
        api_key="test-api-key",
    )

    mock_verify_api_key.assert_called_once_with("test-api-key")
    mock_get_file_tree.assert_called_once_with(
        owner="test-owner", repo="test-repo", ref="main", token="test-token"
    )
    assert len(result) == 2
    assert result[0] == {"path": "src/main.py", "sha": "abc123", "size": 100}
    assert result[1] == {"path": "src/utils.py", "sha": "def456", "size": 200}


def test_get_repository_files_filters_directories(
    mock_verify_api_key, mock_get_file_tree
):
    mock_get_file_tree.return_value = [
        {"path": "src", "sha": "dir123", "type": "tree"},
        {"path": "src/main.py", "sha": "abc123", "size": 100, "type": "blob"},
    ]

    result = get_repository_files(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        token="test-token",
        api_key="test-api-key",
    )

    assert len(result) == 1
    assert result[0]["path"] == "src/main.py"


def test_get_repository_files_handles_missing_size(
    mock_verify_api_key, mock_get_file_tree
):
    mock_get_file_tree.return_value = [
        {"path": "src/main.py", "sha": "abc123", "type": "blob"},
    ]

    result = get_repository_files(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        token="test-token",
        api_key="test-api-key",
    )

    assert len(result) == 1
    assert result[0]["size"] == 0


def test_get_repository_files_invalid_api_key(mock_get_file_tree):
    with patch(
        "services.website.get_repository_files.verify_api_key",
        side_effect=HTTPException(status_code=401, detail="Invalid API key"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_repository_files(
                owner="test-owner",
                repo="test-repo",
                branch="main",
                token="test-token",
                api_key="invalid-key",
            )
        assert exc_info.value.status_code == 401


def test_get_repository_files_empty_tree(mock_verify_api_key, mock_get_file_tree):
    mock_get_file_tree.return_value = []

    result = get_repository_files(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        token="test-token",
        api_key="test-api-key",
    )

    assert result == []


def test_repository_file_typeddict():
    file = RepositoryFile(path="test.py", sha="abc123", size=100)
    assert file["path"] == "test.py"
    assert file["sha"] == "abc123"
    assert file["size"] == 100
    assert isinstance(file, dict)

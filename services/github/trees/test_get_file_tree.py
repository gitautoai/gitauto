import json
import logging
from unittest.mock import Mock, patch
import pytest
import requests
from services.github.trees.get_file_tree import get_file_tree
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def mock_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "tree": [
            {
                "path": "file1.py",
                "mode": "100644",
                "type": "blob",
                "size": 100,
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123"
            }
        ],
        "truncated": False
    }
    return response


@pytest.fixture
def mock_truncated_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "tree": [
            {
                "path": "file1.py",
                "mode": "100644",
                "type": "blob",
                "size": 100,
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123"
            }
        ],
        "truncated": True
    }
    return response


@pytest.fixture
def mock_empty_repo_response():
    response = Mock()
    response.status_code = 409
    response.text = "Git Repository is empty"
    return response


@pytest.fixture
def mock_not_found_response():
    response = Mock()
    response.status_code = 404
    return response


@pytest.fixture
def mock_server_error_response():
    response = Mock()
    response.status_code = 500
    response.reason = "Internal Server Error"
    response.text = "Server error"
    http_error = requests.exceptions.HTTPError()
    http_error.response = response
    return response


@pytest.fixture
def mock_headers():
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "test-app",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def test_get_file_tree_success(mock_response, mock_headers):
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == [
            {
                "path": "file1.py",
                "mode": "100644",
                "type": "blob",
                "size": 100,
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123"
            }
        ]
        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/main",
            headers=mock_headers,
            params={"recursive": 1},
            timeout=120
        )


def test_get_file_tree_empty_repository(mock_empty_repo_response, mock_headers):
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_empty_repo_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == []


def test_get_file_tree_not_found(mock_not_found_response, mock_headers):
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_not_found_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "nonexistent-branch", TOKEN)
        
        assert result == []


def test_get_file_tree_truncated_warning(mock_truncated_response, mock_headers):
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers, \
         patch("services.github.trees.get_file_tree.logging.warning") as mock_warning:
        
        mock_get.return_value = mock_truncated_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == [
            {
                "path": "file1.py",
                "mode": "100644",
                "type": "blob",
                "size": 100,
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123"
            }
        ]
        mock_warning.assert_called_once_with(
            f"Repository tree for `{OWNER}/{REPO}` was truncated by GitHub API. Use the non-recursive method of fetching trees, and fetch one sub-tree at a time. See https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree"
        )


def test_get_file_tree_empty_tree_response(mock_headers):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == []


def test_get_file_tree_exception_handling(mock_headers):
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.side_effect = Exception("Network error")
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == []


def test_get_file_tree_http_error_handling(mock_headers):
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.reason = "Unprocessable Entity"
    mock_response.text = "Validation failed"
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == []


def test_get_file_tree_409_without_empty_message(mock_headers):
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.text = "Some other conflict"
    mock_response.reason = "Conflict"
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == []


def test_get_file_tree_no_truncated_key(mock_headers):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tree": [{"path": "test.py", "mode": "100644", "type": "blob", "size": 50, "sha": "def456", "url": "https://api.github.com/test"}]
    }
    
    with patch("services.github.trees.get_file_tree.requests.get") as mock_get, \
         patch("services.github.trees.get_file_tree.create_headers") as mock_create_headers:
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = get_file_tree(OWNER, REPO, "main", TOKEN)
        
        assert result == [{"path": "test.py", "mode": "100644", "type": "blob", "size": 50, "sha": "def456", "url": "https://api.github.com/test"}]

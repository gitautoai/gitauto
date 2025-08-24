from unittest.mock import Mock, patch
import pytest
import requests
from services.github.trees.create_tree import create_tree
from services.github.types.github_types import BaseArgs
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    return BaseArgs(
        input_from="github",
        owner_type="Organization",
        owner_id=123456789,
        owner=OWNER,
        repo_id=987654321,
        repo=REPO,
        clone_url=f"https://github.com/{OWNER}/{REPO}.git",
        is_fork=False,
        issue_number=1,
        issue_title="Test Issue",
        issue_body="Test issue body",
        issue_comments=[],
        latest_commit_sha="abc123",
        issuer_name="test-user",
        base_branch="main",
        new_branch="feature-branch",
        installation_id=12345678,
        token=TOKEN,
        sender_id=1234567,
        sender_name="test-sender",
        sender_email="test@example.com",
        is_automation=False,
        reviewers=[],
        github_urls=[],
        other_urls=[],
    )


@pytest.fixture
def tree_items():
    return [
        {
            "path": "test_file.py",
            "mode": "100644",
            "type": "blob",
            "content": "print('Hello, World!')",
        },
        {
            "path": "another_file.md",
            "mode": "100644",
            "type": "blob",
            "content": "# Test README",
        },
    ]


@pytest.fixture
def mock_success_response():
    response = Mock()
    response.status_code = 201
    response.json.return_value = {
        "sha": "new_tree_sha_123456",
        "url": f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/new_tree_sha_123456",
        "tree": [
            {
                "path": "test_file.py",
                "mode": "100644",
                "type": "blob",
                "size": 20,
                "sha": "file_sha_123",
                "url": f"https://api.github.com/repos/{OWNER}/{REPO}/git/blobs/file_sha_123",
            }
        ],
    }
    return response


@pytest.fixture
def mock_headers():
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "test-app",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@pytest.fixture
def mock_http_error_response():
    response = Mock()
    response.status_code = 422
    response.reason = "Unprocessable Entity"
    response.text = "Validation failed"
    http_error = requests.exceptions.HTTPError()
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


@pytest.fixture
def mock_not_found_response():
    response = Mock()
    response.status_code = 404
    response.reason = "Not Found"
    response.text = "Repository not found"
    http_error = requests.exceptions.HTTPError()
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


@pytest.fixture
def mock_unauthorized_response():
    response = Mock()
    response.status_code = 401
    response.reason = "Unauthorized"
    response.text = "Bad credentials"
    http_error = requests.exceptions.HTTPError()
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    return response


def test_create_tree_success(base_args, tree_items, mock_success_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result == "new_tree_sha_123456"
        
        expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees"
        expected_tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        
        mock_post.assert_called_once_with(
            url=expected_url,
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )
        mock_create_headers.assert_called_once_with(token=TOKEN)


def test_create_tree_empty_tree_items(base_args, mock_success_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    empty_tree_items = []
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, empty_tree_items)
        
        assert result == "new_tree_sha_123456"
        
        expected_tree_data = {
            "base_tree": base_tree_sha,
            "tree": empty_tree_items
        }
        
        mock_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )


def test_create_tree_http_error_handling(base_args, tree_items, mock_http_error_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_http_error_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_not_found_error(base_args, tree_items, mock_not_found_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_not_found_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_unauthorized_error(base_args, tree_items, mock_unauthorized_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_unauthorized_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_network_exception_handling(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_timeout_exception_handling(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_json_decode_error_handling(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_missing_sha_in_response(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "url": f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/new_tree_sha_123456",
        "tree": []
    }  # Missing 'sha' key
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result is None


def test_create_tree_rate_limit_error(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "API rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1234567890"
    }
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers, patch("time.time") as mock_time, patch("time.sleep") as mock_sleep:
        
        mock_post.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        mock_time.return_value = 1234567880  # 10 seconds before reset
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        # The function should handle rate limiting and eventually return None
        assert result is None
        mock_sleep.assert_called()


def test_create_tree_large_tree_items(base_args, mock_success_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    # Create a large list of tree items
    large_tree_items = [
        {
            "path": f"file_{i}.py",
            "mode": "100644",
            "type": "blob",
            "content": f"# File {i}\nprint('File {i}')",
        }
        for i in range(100)
    ]
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, large_tree_items)
        
        assert result == "new_tree_sha_123456"
        
        expected_tree_data = {
            "base_tree": base_tree_sha,
            "tree": large_tree_items
        }
        
        mock_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )


def test_create_tree_with_different_file_modes(base_args, mock_success_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    tree_items_with_modes = [
        {
            "path": "executable_script.sh",
            "mode": "100755",  # Executable file
            "type": "blob",
            "content": "#!/bin/bash\necho 'Hello World'",
        },
        {
            "path": "regular_file.txt",
            "mode": "100644",  # Regular file
            "type": "blob",
            "content": "Regular text file",
        },
        {
            "path": "symlink",
            "mode": "120000",  # Symbolic link
            "type": "blob",
            "content": "target_file.txt",
        },
    ]
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items_with_modes)
        
        assert result == "new_tree_sha_123456"
        
        expected_tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items_with_modes
        }
        
        mock_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )


def test_create_tree_with_tree_references(base_args, mock_success_response, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    tree_items_with_tree_refs = [
        {
            "path": "subdir",
            "mode": "040000",  # Directory/tree mode
            "type": "tree",
            "sha": "existing_tree_sha_456",
        },
        {
            "path": "file.py",
            "mode": "100644",
            "type": "blob",
            "content": "print('Hello')",
        },
    ]
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items_with_tree_refs)
        
        assert result == "new_tree_sha_123456"
        
        expected_tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items_with_tree_refs
        }
        
        mock_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )


def test_create_tree_server_error_handling(base_args, tree_items, mock_headers):
    base_tree_sha = "base_tree_sha_123"
    
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error occurred"
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        # 500 errors should return None without logging (as per handle_exceptions)
        assert result is None


def test_create_tree_with_none_base_tree_sha(base_args, tree_items, mock_success_response, mock_headers):
    # Test with None as base_tree_sha (creating tree from scratch)
    base_tree_sha = None
    
    with patch("services.github.trees.create_tree.requests.post") as mock_post, patch(
        "services.github.trees.create_tree.create_headers"
    ) as mock_create_headers:
        
        mock_post.return_value = mock_success_response
        mock_create_headers.return_value = mock_headers
        
        result = create_tree(base_args, base_tree_sha, tree_items)
        
        assert result == "new_tree_sha_123456"
        
        expected_tree_data = {
            "base_tree": None,
            "tree": tree_items
        }
        
        mock_post.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
            json=expected_tree_data,
            headers=mock_headers,
            timeout=120
        )
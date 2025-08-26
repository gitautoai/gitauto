# Standard imports
import json
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
import requests

# Local imports
from services.github.trees.create_tree import create_tree


@pytest.fixture
def base_args():
    """Create a mock BaseArgs dictionary for testing."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token",
        "input_from": "github",
        "owner_type": "Organization",
        "owner_id": 123456789,
        "repo_id": 987654321,
        "clone_url": "https://github.com/test-owner/test-repo.git",
        "is_fork": False,
        "issue_number": 1,
        "issue_title": "Test Issue",
        "issue_body": "Test issue body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "issuer_name": "test-user",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345678,
        "sender_id": 1234567,
        "sender_name": "test-sender",
        "sender_email": "test@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
    }


@pytest.fixture
def tree_items():
    """Create sample tree items for testing."""
    return [
        {
            "path": "file1.py",
            "mode": "100644",
            "type": "blob",
            "content": "print('Hello, World!')",
        },
        {
            "path": "file2.js",
            "mode": "100644",
            "type": "blob",
            "content": "console.log('Hello, World!');",
        },
    ]


@pytest.fixture
def mock_response_success():
    """Create a successful mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "sha": "new-tree-sha-123456",
        "url": "https://api.github.com/repos/test-owner/test-repo/git/trees/new-tree-sha-123456",
        "tree": [
            {
                "path": "file1.py",
                "mode": "100644",
                "type": "blob",
                "sha": "blob-sha-1",
                "size": 21,
                "url": "https://api.github.com/repos/test-owner/test-repo/git/blobs/blob-sha-1",
            },
            {
                "path": "file2.js",
                "mode": "100644",
                "type": "blob",
                "sha": "blob-sha-2",
                "size": 26,
                "url": "https://api.github.com/repos/test-owner/test-repo/git/blobs/blob-sha-2",
            },
        ],
        "truncated": False,
    }
    return mock_response


@pytest.fixture
def mock_response_400():
    """Create a 400 Bad Request mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.reason = "Bad Request"
    mock_response.text = "Invalid tree data"
    http_error = requests.exceptions.HTTPError("400 Client Error: Bad Request")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@pytest.fixture
def mock_response_401():
    """Create a 401 Unauthorized mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.reason = "Unauthorized"
    mock_response.text = "Bad credentials"
    http_error = requests.exceptions.HTTPError("401 Client Error: Unauthorized")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@pytest.fixture
def mock_response_403():
    """Create a 403 Forbidden mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Forbidden"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
    }
    http_error = requests.exceptions.HTTPError("403 Client Error: Forbidden")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@pytest.fixture
def mock_response_404():
    """Create a 404 Not Found mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Repository not found"
    http_error = requests.exceptions.HTTPError("404 Client Error: Not Found")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@pytest.fixture
def mock_response_422():
    """Create a 422 Unprocessable Entity mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.reason = "Unprocessable Entity"
    mock_response.text = "Validation Failed"
    http_error = requests.exceptions.HTTPError("422 Client Error: Unprocessable Entity")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@pytest.fixture
def mock_response_500():
    """Create a 500 Internal Server Error mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Internal Server Error"
    http_error = requests.exceptions.HTTPError("500 Server Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_successful_tree_creation(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_success
):
    """Test successful tree creation."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_success

    result = create_tree(base_args, "base-tree-sha", tree_items)

    assert result == "new-tree-sha-123456"
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/git/trees",
        json={"base_tree": "base-tree-sha", "tree": tree_items},
        headers={"Authorization": "Bearer test-token"},
        timeout=120,  # TIMEOUT constant from config
    )
    mock_response_success.raise_for_status.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_empty_tree_items(
    mock_create_headers, mock_requests_post, base_args, mock_response_success
):
    """Test tree creation with empty tree items."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_response_success.json.return_value = {"sha": "empty-tree-sha"}
    mock_requests_post.return_value = mock_response_success

    result = create_tree(base_args, "base-tree-sha", [])

    assert result == "empty-tree-sha"
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/git/trees",
        json={"base_tree": "base-tree-sha", "tree": []},
        headers={"Authorization": "Bearer test-token"},
        timeout=120,
    )


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_large_tree_items(
    mock_create_headers, mock_requests_post, base_args, mock_response_success
):
    """Test tree creation with many tree items."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_success

    # Create a large number of tree items
    large_tree_items = [
        {
            "path": f"file{i}.py",
            "mode": "100644",
            "type": "blob",
            "content": f"print('File {i}')",
        }
        for i in range(100)
    ]

    result = create_tree(base_args, "base-tree-sha", large_tree_items)

    assert result == "new-tree-sha-123456"
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/git/trees",
        json={"base_tree": "base-tree-sha", "tree": large_tree_items},
        headers={"Authorization": "Bearer test-token"},
        timeout=120,
    )


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_bad_request_400(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_400
):
    """Test handling of 400 Bad Request error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_400

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_unauthorized_401(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_401
):
    """Test handling of 401 Unauthorized error."""
    mock_create_headers.return_value = {"Authorization": "Bearer invalid-token"}
    mock_requests_post.return_value = mock_response_401

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_forbidden_403_rate_limit(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_403
):
    """Test handling of 403 Forbidden error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_403

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_not_found_404(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_404
):
    """Test handling of 404 Not Found error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_404

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_unprocessable_entity_422(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_422
):
    """Test handling of 422 Unprocessable Entity error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_422

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_server_error_500(
    mock_create_headers, mock_requests_post, base_args, tree_items, mock_response_500
):
    """Test handling of 500 Internal Server Error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_500

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the HTTPError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_json_decode_error(
    mock_create_headers, mock_requests_post, base_args, tree_items
):
    """Test handling of JSON decode error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
    mock_requests_post.return_value = mock_response

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the JSONDecodeError and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_connection_error(mock_create_headers, mock_requests_post, base_args, tree_items):
    """Test handling of connection error."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the connection error and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_post.assert_called_once()


@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_create_headers_exception(mock_create_headers, mock_requests_post, base_args, tree_items):
    """Test handling of create_headers exception."""
    mock_create_headers.side_effect = Exception("Header creation failed")

    result = create_tree(base_args, "base-tree-sha", tree_items)

    # The handle_exceptions decorator should catch the exception and return None
    assert result is None
    mock_create_headers.assert_called_once_with(token="test-token")
    # requests.post should not be called if create_headers fails
    mock_requests_post.assert_not_called()


@pytest.mark.parametrize(
    "owner,repo,base_tree_sha",
    [
        ("test-owner", "test-repo", "base-sha-123"),
        ("org-name", "repo-name", "different-base-sha"),
        ("user123", "project_name", "another-sha-456"),
        ("owner-with-dashes", "repo.with.dots", "sha-with-numbers-789"),
        ("CamelCaseOwner", "CamelCaseRepo", "CamelCaseSha123"),
    ],
)
@patch("services.github.trees.create_tree.requests.post")
@patch("services.github.trees.create_tree.create_headers")
def test_various_parameter_combinations(
    mock_create_headers,
    mock_requests_post,
    mock_response_success,
    base_args,
    tree_items,
    owner,
    repo,
    base_tree_sha,
):
    """Test that the function handles various parameter combinations correctly."""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
    mock_requests_post.return_value = mock_response_success

    # Update base_args with test parameters
    base_args["owner"] = owner
    base_args["repo"] = repo

    result = create_tree(base_args, base_tree_sha, tree_items)

    assert result == "new-tree-sha-123456"
    expected_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees"
    mock_requests_post.assert_called_once_with(
        url=expected_url,
        json={"base_tree": base_tree_sha, "tree": tree_items},
        headers={"Authorization": "Bearer test-token"},
        timeout=120,
    )

"""Unit tests for update_pull_request_body function.

Related Documentation:
https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request
"""

from unittest.mock import patch, MagicMock
import pytest
import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from config import TIMEOUT
from services.github.pulls.update_pull_request_body import update_pull_request_body


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": 12345, "body": "Updated body"}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@pytest.fixture
def sample_url():
    """Fixture to provide a sample PR URL."""
    return "https://api.github.com/repos/owner/repo/pulls/123"


@pytest.fixture
def sample_token():
    """Fixture to provide a sample token."""
    return "ghp_test_token_123456789"


@pytest.fixture
def sample_body():
    """Fixture to provide a sample PR body."""
    return "This is an updated PR description."


def test_update_pull_request_body_successful_request(mock_response, sample_url, sample_token, sample_body):
    """Test successful API request returns the response JSON."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result == {"id": 12345, "body": "Updated body"}


def test_update_pull_request_body_calls_correct_endpoint(sample_url, sample_token, sample_body):
    """Test that the function calls the correct GitHub API endpoint."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": sample_body}
        mock_patch.return_value = mock_response

        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["url"] == sample_url


def test_update_pull_request_body_uses_correct_headers(sample_url, sample_token, sample_body):
    """Test that the function uses correct headers including authorization."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch, \
         patch("services.github.pulls.update_pull_request_body.create_headers") as mock_create_headers:

        mock_headers = {"Authorization": f"Bearer {sample_token}"}
        mock_create_headers.return_value = mock_headers
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": sample_body}
        mock_patch.return_value = mock_response

        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)

        mock_create_headers.assert_called_once_with(token=sample_token)
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["headers"] == mock_headers


def test_update_pull_request_body_sends_correct_data(sample_url, sample_token, sample_body):
    """Test that the function sends the correct data in the request."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": sample_body}
        mock_patch.return_value = mock_response

        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["json"] == {"body": sample_body}


def test_update_pull_request_body_uses_correct_timeout(sample_url, sample_token, sample_body):
    """Test that the function uses the configured timeout."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": sample_body}
        mock_patch.return_value = mock_response

        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["timeout"] == TIMEOUT


def test_update_pull_request_body_calls_raise_for_status(mock_response, sample_url, sample_token, sample_body):
    """Test that the function calls raise_for_status on the response."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        mock_response.raise_for_status.assert_called_once()


def test_update_pull_request_body_calls_json_on_response(mock_response, sample_url, sample_token, sample_body):
    """Test that the function calls json() on the response."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        mock_response.json.assert_called_once()


def test_update_pull_request_body_http_error_returns_none(sample_url, sample_token, sample_body):
    """Test that HTTP errors are handled and return None due to decorator."""
    mock_response = MagicMock()
    # Create a proper HTTPError with a response object
    http_error = HTTPError("404 Not Found")
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.reason = "Not Found"
    error_response.text = "Pull request not found"
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    http_error.response = error_response

    mock_response.raise_for_status.side_effect = http_error
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_request_exception_returns_none(sample_url, sample_token, sample_body):
    """Test that request exceptions are handled and return None due to decorator."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch", 
               side_effect=RequestException("Network error")):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_timeout_returns_none(sample_url, sample_token, sample_body):
    """Test that timeout exceptions are handled and return None due to decorator."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch", 
               side_effect=Timeout("Request timed out")):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_json_decode_error_returns_none(sample_url, sample_token, sample_body):
    """Test that JSON decode errors are handled and return None due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_with_empty_body(sample_url, sample_token):
    """Test that the function handles empty body string."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": ""}
        mock_patch.return_value = mock_response

        result = update_pull_request_body(url=sample_url, token=sample_token, body="")

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["json"] == {"body": ""}
        assert result == {"id": 12345, "body": ""}


def test_update_pull_request_body_with_long_body(sample_url, sample_token):
    """Test that the function handles long body text."""
    long_body = "A" * 10000  # 10,000 character string
    
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": long_body}
        mock_patch.return_value = mock_response

        result = update_pull_request_body(url=sample_url, token=sample_token, body=long_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["json"] == {"body": long_body}
        assert result == {"id": 12345, "body": long_body}


def test_update_pull_request_body_with_special_characters(sample_url, sample_token):
    """Test that the function handles body with special characters."""
    special_body = "Special characters: !@#$%^&*()_+-=[]{}|;:'\",.<>/?\n\t"
    
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": special_body}
        mock_patch.return_value = mock_response

        result = update_pull_request_body(url=sample_url, token=sample_token, body=special_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["json"] == {"body": special_body}
        assert result == {"id": 12345, "body": special_body}


def test_update_pull_request_body_with_markdown_content(sample_url, sample_token):
    """Test that the function handles body with markdown content."""
    markdown_body = """# Heading
    
## Subheading

- List item 1
- List item 2

```python
def code_example():
    return "Hello World"
```

[Link text](https://example.com)
"""
    
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": markdown_body}
        mock_patch.return_value = mock_response

        result = update_pull_request_body(url=sample_url, token=sample_token, body=markdown_body)

        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert kwargs["json"] == {"body": markdown_body}
        assert result == {"id": 12345, "body": markdown_body}


def test_update_pull_request_body_rate_limit_exceeded(sample_url, sample_token, sample_body):
    """Test handling of rate limit exceeded error."""
    mock_response = MagicMock()
    http_error = HTTPError("403 Forbidden")
    error_response = MagicMock()
    error_response.status_code = 403
    error_response.reason = "Forbidden"
    error_response.text = "API rate limit exceeded"
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1609459200"  # Some future timestamp
    }
    http_error.response = error_response

    mock_response.raise_for_status.side_effect = http_error
    
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response), \
         patch("services.github.pulls.update_pull_request_body.time.sleep") as mock_sleep, \
         patch("services.github.pulls.update_pull_request_body.time.time", return_value=1609459100):
        
        # This should return None due to the decorator's handling
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_secondary_rate_limit_exceeded(sample_url, sample_token, sample_body):
    """Test handling of secondary rate limit exceeded error."""
    mock_response = MagicMock()
    http_error = HTTPError("403 Forbidden")
    error_response = MagicMock()
    error_response.status_code = 403
    error_response.reason = "Forbidden"
    error_response.text = "You have exceeded a secondary rate limit"
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4990",
        "X-RateLimit-Used": "10",
        "Retry-After": "60"
    }
    http_error.response = error_response

    mock_response.raise_for_status.side_effect = http_error
    
    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response), \
         patch("services.github.pulls.update_pull_request_body.time.sleep") as mock_sleep:
        
        # This should return None due to the decorator's handling
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None


def test_update_pull_request_body_with_complete_github_response(sample_url, sample_token, sample_body):
    """Test with a complete GitHub API response structure."""
    complete_response = {
        "url": sample_url,
        "id": 12345,
        "node_id": "PR_kwDOA1YEwc5IZvtx",
        "html_url": "https://github.com/owner/repo/pull/123",
        "diff_url": "https://github.com/owner/repo/pull/123.diff",
        "patch_url": "https://github.com/owner/repo/pull/123.patch",
        "issue_url": "https://api.github.com/repos/owner/repo/issues/123",
        "number": 123,
        "state": "open",
        "locked": False,
        "title": "Example Pull Request",
        "user": {
            "login": "octocat",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "",
            "url": "https://api.github.com/users/octocat",
            "html_url": "https://github.com/octocat",
            "type": "User",
            "site_admin": False
        },
        "body": sample_body,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "merge_commit_sha": "e5bd3914e2e596debea16f433f57875b5b90bcd6",
        "assignee": None,
        "assignees": [],
        "requested_reviewers": [],
        "requested_teams": [],
        "labels": [],
        "milestone": None,
        "draft": False,
        "commits_url": "https://api.github.com/repos/owner/repo/pulls/123/commits",
        "review_comments_url": "https://api.github.com/repos/owner/repo/pulls/123/comments",
        "review_comment_url": "https://api.github.com/repos/owner/repo/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/owner/repo/issues/123/comments",
        "statuses_url": "https://api.github.com/repos/owner/repo/statuses/e5bd3914e2e596debea16f433f57875b5b90bcd6",
        "head": {
            "label": "owner:feature-branch",
            "ref": "feature-branch",
            "sha": "e5bd3914e2e596debea16f433f57875b5b90bcd6",
            "repo": {
                "id": 1296269,
                "name": "repo",
                "full_name": "owner/repo",
                "owner": {
                    "login": "owner",
                    "id": 1,
                    "type": "User"
                },
                "html_url": "https://github.com/owner/repo"
            }
        },
        "base": {
            "label": "owner:main",
            "ref": "main",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "repo": {
                "id": 1296269,
                "name": "repo",
                "full_name": "owner/repo",
                "owner": {
                    "login": "owner",
                    "id": 1,
                    "type": "User"
                },
                "html_url": "https://github.com/owner/repo"
            }
        },
        "author_association": "OWNER",
        "auto_merge": None,
        "active_lock_reason": None
    }

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = complete_response

    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result == complete_response
        assert result["body"] == sample_body
        assert result["id"] == 12345
        assert result["number"] == 123


@pytest.mark.parametrize("url,token,body", [
    ("https://api.github.com/repos/owner/repo/pulls/1", "token1", "body1"),
    ("https://api.github.com/repos/owner/repo/pulls/2", "token2", "body2"),
    ("https://api.github.com/repos/owner/repo/pulls/3", "token3", "body3"),
])
def test_update_pull_request_body_with_various_inputs(url, token, body):
    """Test the function with various input combinations using parametrize."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"id": 12345, "body": body}

    with patch("services.github.pulls.update_pull_request_body.requests.patch", return_value=mock_response):
        result = update_pull_request_body(url=url, token=token, body=body)
        assert result["body"] == body


def test_update_pull_request_body_decorator_behavior(sample_url, sample_token, sample_body):
    """Test that the handle_exceptions decorator is properly applied."""
    # Test that the function has the decorator applied by checking it returns None on exception
    with patch("services.github.pulls.update_pull_request_body.requests.patch", 
               side_effect=Exception("Unexpected error")):
        result = update_pull_request_body(url=sample_url, token=sample_token, body=sample_body)
        assert result is None
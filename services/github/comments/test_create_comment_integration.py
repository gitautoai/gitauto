import pytest
import responses
import json
import time

from services.github.comments.create_comment import create_comment
from services.github.create_headers import create_headers
from tests.constants import OWNER, REPO, TOKEN
from config import GITHUB_API_URL, TIMEOUT


@responses.activate
def test_create_comment_integration_success():
    """Test successful comment creation with GitHub input using responses library."""
    # Arrange
    body = "Test comment body"
    issue_number = 123
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
        "input_from": "github"
    }
    
    expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments/1"
    mock_response = {
        "url": expected_url,
        "html_url": f"https://github.com/{OWNER}/{REPO}/issues/{issue_number}#issuecomment-1",
        "id": 1,
        "node_id": "MDEyOklzc3VlQ29tbWVudDE=",
        "user": {
            "login": "octocat",
            "id": 1,
        },
        "created_at": "2011-04-14T16:00:49Z",
        "updated_at": "2011-04-14T16:00:49Z",
        "body": body
    }
    
    # Register the mock response
    responses.add(
        responses.POST,
        f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments",
        json=mock_response,
        status=201,
        content_type="application/json"
    )
    
    # Act
    result = create_comment(body, base_args)
    
    # Assert
    assert result == expected_url
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
    
    # Verify request headers and body
    request_headers = responses.calls[0].request.headers
    assert request_headers["Authorization"] == f"Bearer {TOKEN}"
    
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body == {"body": body}


@responses.activate
def test_create_comment_integration_error():
    """Test error handling when GitHub API returns an error."""
    # Arrange
    body = "Test comment body"
    issue_number = 123
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
        "input_from": "github"
    }
    
    # Register the mock error response
    responses.add(
        responses.POST,
        f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments",
        json={"message": "Not Found", "documentation_url": "https://docs.github.com/rest/reference/issues#create-an-issue-comment"},
        status=404,
        content_type="application/json"
    )
    
    # Act
    result = create_comment(body, base_args)
    
    # Assert
    assert result is None  # Default return value from handle_exceptions
    assert len(responses.calls) == 1


@responses.activate
def test_create_comment_integration_malformed_response():
    """Test error handling when GitHub API returns a malformed response."""
    # Arrange
    body = "Test comment body"
    issue_number = 123
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
        "input_from": "github"
    }
    
    # Register the mock response with malformed JSON
    responses.add(
        responses.POST,
        f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments",
        body="Not a valid JSON",
        status=200,
        content_type="application/json"
    )
    
    # Act
    result = create_comment(body, base_args)
    
    # Assert
    assert result is None  # Default return value from handle_exceptions
    assert len(responses.calls) == 1


def test_create_comment_integration_jira():
    """Test comment creation with Jira input (no actual API call)."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "jira"
    }
    
    # Act
    result = create_comment(body, base_args)
    
    # Assert
    assert result is None


@responses.activate
def test_create_comment_integration_rate_limit():
    """Test error handling when GitHub API rate limit is exceeded."""
    # Arrange
    body = "Test comment body"
    issue_number = 123
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
        "input_from": "github"
    }
    
    # Register the mock rate limit response
    responses.add(
        responses.POST,
        f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments",
        json={
            "message": "API rate limit exceeded",
            "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
        },
        status=403,
        headers={
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": str(int(time.time()) + 3600)  # Reset in 1 hour
        },
        content_type="application/json"
    )
    
    # Act
    # Note: In a real scenario, this would retry after waiting, but for testing we just check the result
    result = create_comment(body, base_args)
    
    # Assert
    assert result is None  # Default return value from handle_exceptions
    assert len(responses.calls) == 1
import pytest
from unittest.mock import patch, MagicMock
import requests

from services.github.issues.create_issue import create_issue
from tests.constants import OWNER, REPO, TOKEN


def test_create_issue_success_with_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        result = create_issue("Test Title", "Test Body", ["user1", "user2"], base_args)
    
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert call_args.kwargs["json"]["assignees"] == ["user1", "user2"]
    mock_response.raise_for_status.assert_called_once()
    assert result is None


def test_create_issue_success_without_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        result = create_issue("Test Title", "Test Body", [], base_args)
    
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.raise_for_status.assert_called_once()
    assert result is None


def test_create_issue_success_with_empty_assignees_list():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        result = create_issue("Test Title", "Test Body", [], base_args)
    
    call_args = mock_post.call_args
    assert "assignees" not in call_args.kwargs["json"]
    assert result is None


def test_create_issue_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        result = create_issue("Test Title", "Test Body", ["user1"], base_args)
    
    mock_response.raise_for_status.assert_called_once()
    assert result is None


def test_create_issue_request_exception():
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.side_effect = requests.RequestException("Connection error")
        
        result = create_issue("Test Title", "Test Body", ["user1"], base_args)
    
    assert result is None


def test_create_issue_with_none_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        result = create_issue("Test Title", "Test Body", None, base_args)
    
    call_args = mock_post.call_args
    assert "assignees" not in call_args[1]["json"]
    assert result is None


def test_create_issue_api_url_construction():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token"
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.GITHUB_API_URL", "https://api.github.com"), \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_post.return_value = mock_response
        
        create_issue("Test Title", "Test Body", ["user1"], base_args)
    
    call_args = mock_post.call_args
    assert call_args.kwargs["url"] == "https://api.github.com/repos/test-owner/test-repo/issues"


def test_create_issue_timeout_parameter():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.TIMEOUT", 60), \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        
        create_issue("Test Title", "Test Body", ["user1"], base_args)
    
    call_args = mock_post.call_args
    assert call_args[1]["timeout"] == 60


def test_create_issue_headers_creation():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": "test-token-123"
    }
    
    with patch("services.github.issues.create_issue.requests.post") as mock_post, \
         patch("services.github.issues.create_issue.create_headers") as mock_create_headers, \
         patch("services.github.issues.create_issue.PRODUCT_ID", "test-product-id"):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token-123"}
        mock_post.return_value = mock_response
        
        create_issue("Test Title", "Test Body", [], base_args)
    
    mock_create_headers.assert_called_once_with(token="test-token-123")
    call_args = mock_post.call_args
    assert call_args[1]["headers"] == {"Authorization": "Bearer test-token-123"}

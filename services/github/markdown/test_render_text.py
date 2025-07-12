from unittest.mock import patch, MagicMock
import pytest
import requests
from requests import HTTPError

from config import GITHUB_API_URL, TIMEOUT
from services.github.markdown.render_text import render_text
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_base_args():
    """Fixture providing test BaseArgs."""
    return BaseArgs(
        owner="test-owner",
        repo="test-repo", 
        token="test-token-123"
    )


@pytest.fixture
def mock_response():
    """Fixture providing a mock response object."""
    response = MagicMock()
    response.text = "<p>Rendered markdown content</p>"
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def mock_headers():
    """Fixture providing mock headers."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test-token-123",
        "User-Agent": "test-app",
        "X-GitHub-Api-Version": "2022-11-28"
    }


@pytest.fixture
def mock_post_request(mock_response):
    """Fixture providing a mocked post request."""
    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_create_headers(mock_headers):
    """Fixture providing mocked create_headers function."""
    with patch("services.github.markdown.render_text.create_headers") as mock_headers_func:
        mock_headers_func.return_value = mock_headers
        yield mock_headers_func


def test_render_text_successful_request(mock_base_args, mock_post_request, mock_create_headers):
    """Test successful markdown rendering."""
    text = "# Hello World\nThis is a test."
    
    result = render_text(mock_base_args, text)
    
    assert result == "<p>Rendered markdown content</p>"
    mock_create_headers.assert_called_once_with(token="test-token-123")
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={
            "text": text,
            "mode": "gfm",
            "context": "test-owner/test-repo"
        },
        timeout=TIMEOUT
    )


def test_render_text_with_empty_text(mock_base_args, mock_post_request, mock_create_headers):
    """Test rendering with empty text."""
    text = ""
    
    result = render_text(mock_base_args, text)
    
    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={
            "text": "",
            "mode": "gfm",
            "context": "test-owner/test-repo"
        },
        timeout=TIMEOUT
    )


def test_render_text_with_complex_markdown(mock_base_args, mock_post_request, mock_create_headers):
    """Test rendering with complex markdown content."""
    text = """# Title

## Subtitle

- List item 1
- List item 2

```python
def hello():
    print("Hello World")
```

[Link](https://example.com)
"""
    
    result = render_text(mock_base_args, text)
    
    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={
            "text": text,
            "mode": "gfm",
            "context": "test-owner/test-repo"
        },
        timeout=TIMEOUT
    )


def test_render_text_with_special_characters(mock_base_args, mock_post_request, mock_create_headers):
    """Test rendering with special characters and unicode."""
    text = "# 测试 🚀\n\nSpecial chars: @#$%^&*()_+-=[]{}|;:,.<>?"
    
    result = render_text(mock_base_args, text)
    
    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={
            "text": text,
            "mode": "gfm",
            "context": "test-owner/test-repo"
        },
        timeout=TIMEOUT
    )


def test_render_text_extracts_correct_base_args_values(mock_post_request, mock_create_headers):
    """Test that function correctly extracts values from BaseArgs."""
    base_args = BaseArgs(
        owner="different-owner",
        repo="different-repo",
        token="different-token-456"
    )
    text = "Test content"
    
    render_text(base_args, text)
    
    mock_create_headers.assert_called_once_with(token="different-token-456")
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={
            "text": text,
            "mode": "gfm",
            "context": "different-owner/different-repo"
        },
        timeout=TIMEOUT
    )


def test_render_text_uses_correct_api_endpoint(mock_base_args, mock_post_request, mock_create_headers):
    """Test that the correct GitHub API endpoint is used."""
    text = "Test"
    
    render_text(mock_base_args, text)
    
    expected_url = f"{GITHUB_API_URL}/markdown"
    mock_post_request.assert_called_once()
    call_args = mock_post_request.call_args
    assert call_args[1]["url"] == expected_url


def test_render_text_uses_gfm_mode(mock_base_args, mock_post_request, mock_create_headers):
    """Test that GitHub Flavored Markdown mode is used."""
    text = "Test"
    
    render_text(mock_base_args, text)
    
    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["mode"] == "gfm"


def test_render_text_http_error_returns_empty_string(mock_base_args, mock_create_headers):
    """Test that HTTP errors return empty string due to handle_exceptions decorator."""
    text = "Test content"
    
    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        result = render_text(mock_base_args, text)
        
        # Due to handle_exceptions decorator with default_return_value="", should return empty string
        assert result == ""


def test_render_text_request_exception_returns_empty_string(mock_base_args, mock_create_headers):
    """Test that request exceptions return empty string due to handle_exceptions decorator."""
    text = "Test content"
    
    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_post.side_effect = requests.RequestException("Connection error")
        
        result = render_text(mock_base_args, text)
        
        # Due to handle_exceptions decorator with default_return_value="", should return empty string
        assert result == ""


def test_render_text_response_calls_raise_for_status(mock_base_args, mock_post_request, mock_create_headers):
    """Test that response.raise_for_status() is called."""
    text = "Test content"
    
    render_text(mock_base_args, text)
    
    mock_post_request.return_value.raise_for_status.assert_called_once()


def test_render_text_returns_response_text(mock_base_args, mock_create_headers):
    """Test that the function returns the response text."""
    text = "Test content"
    expected_response = "<h1>Rendered HTML</h1>"
    
    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_response = MagicMock()
        mock_response.text = expected_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = render_text(mock_base_args, text)
        
        assert result == expected_response
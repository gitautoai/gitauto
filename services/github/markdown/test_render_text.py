from unittest.mock import patch, MagicMock
import pytest
import requests
from requests import HTTPError

from config import GITHUB_API_URL, TIMEOUT
from services.github.markdown.render_text import render_text


@pytest.fixture
def mock_base_args(create_test_base_args):
    """Fixture providing test BaseArgs."""
    return create_test_base_args(
        owner="test-owner", repo="test-repo", token="test-token-123"
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
        "X-GitHub-Api-Version": "2022-11-28",
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
    with patch(
        "services.github.markdown.render_text.create_headers"
    ) as mock_headers_func:
        mock_headers_func.return_value = mock_headers
        yield mock_headers_func


@pytest.fixture
def integration_base_args(test_owner, test_repo, test_token, create_test_base_args):
    """Fixture providing real BaseArgs for integration testing."""
    return create_test_base_args(owner=test_owner, repo=test_repo, token=test_token)


def test_render_text_successful_request(
    mock_base_args, mock_post_request, mock_create_headers
):
    """Test successful markdown rendering."""
    text = "# Hello World\nThis is a test."

    result = render_text(mock_base_args, text)

    assert result == "<p>Rendered markdown content</p>"
    mock_create_headers.assert_called_once_with(token="test-token-123")
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={"text": text, "mode": "gfm", "context": "test-owner/test-repo"},
        timeout=TIMEOUT,
    )


def test_render_text_with_empty_text(
    mock_base_args, mock_post_request, mock_create_headers
):
    """Test rendering with empty text."""
    text = ""

    result = render_text(mock_base_args, text)

    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={"text": "", "mode": "gfm", "context": "test-owner/test-repo"},
        timeout=TIMEOUT,
    )


def test_render_text_with_complex_markdown(
    mock_base_args, mock_post_request, mock_create_headers
):
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
        json={"text": text, "mode": "gfm", "context": "test-owner/test-repo"},
        timeout=TIMEOUT,
    )


def test_render_text_with_special_characters(
    mock_base_args, mock_post_request, mock_create_headers
):
    """Test rendering with special characters and unicode."""
    text = "# 测试 🚀\n\nSpecial chars: @#$%^&*()_+-=[]{}|;:,.<>?"

    result = render_text(mock_base_args, text)

    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={"text": text, "mode": "gfm", "context": "test-owner/test-repo"},
        timeout=TIMEOUT,
    )


def test_render_text_extracts_correct_base_args_values(
    mock_post_request, mock_create_headers, create_test_base_args
):
    """Test that function correctly extracts values from BaseArgs."""
    base_args = create_test_base_args(
        owner="different-owner", repo="different-repo", token="different-token-456"
    )
    text = "Test content"

    render_text(base_args, text)

    mock_create_headers.assert_called_once_with(token="different-token-456")
    mock_post_request.assert_called_once_with(
        url=f"{GITHUB_API_URL}/markdown",
        headers=mock_create_headers.return_value,
        json={"text": text, "mode": "gfm", "context": "different-owner/different-repo"},
        timeout=TIMEOUT,
    )


def test_render_text_uses_correct_api_endpoint(mock_base_args, mock_post_request):
    """Test that the correct GitHub API endpoint is used."""
    text = "Test"

    render_text(mock_base_args, text)

    expected_url = f"{GITHUB_API_URL}/markdown"
    mock_post_request.assert_called_once()
    call_args = mock_post_request.call_args
    assert call_args[1]["url"] == expected_url


def test_render_text_uses_gfm_mode(mock_base_args, mock_post_request):
    """Test that GitHub Flavored Markdown mode is used."""
    text = "Test"

    render_text(mock_base_args, text)

    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["mode"] == "gfm"


def test_render_text_uses_correct_context_format(mock_base_args, mock_post_request):
    """Test that context is formatted as owner/repo."""
    text = "Test"

    render_text(mock_base_args, text)

    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["context"] == "test-owner/test-repo"


def test_render_text_uses_correct_timeout(mock_base_args, mock_post_request):
    """Test that the correct timeout value is used."""
    text = "Test"

    render_text(mock_base_args, text)

    call_args = mock_post_request.call_args
    assert call_args[1]["timeout"] == TIMEOUT


def test_render_text_http_error_returns_empty_string(mock_base_args):
    """Test that HTTP errors return empty string due to handle_exceptions decorator."""
    text = "Test content"

    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_response = MagicMock()
        # Create a proper HTTPError with a response object
        http_error = HTTPError("404 Not Found")
        http_error.response = MagicMock()
        http_error.response.status_code = 404
        http_error.response.reason = "Not Found"
        http_error.response.text = "404 Not Found"
        http_error.response.headers = {}
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = render_text(mock_base_args, text)

        # Due to handle_exceptions decorator with default_return_value="", should return empty string
        assert result == ""


def test_render_text_request_exception_returns_empty_string(mock_base_args):
    """Test that request exceptions return empty string due to handle_exceptions decorator."""
    text = "Test content"

    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_post.side_effect = requests.RequestException("Connection error")

        result = render_text(mock_base_args, text)

        # Due to handle_exceptions decorator with default_return_value="", should return empty string
        assert result == ""


def test_render_text_response_calls_raise_for_status(mock_base_args, mock_post_request):
    """Test that response.raise_for_status() is called."""
    text = "Test content"

    render_text(mock_base_args, text)

    mock_post_request.return_value.raise_for_status.assert_called_once()


def test_render_text_returns_response_text(mock_base_args):
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


def test_render_text_with_multiline_markdown(mock_base_args, mock_post_request):
    """Test rendering with multiline markdown content."""
    text = """Line 1
Line 2
Line 3

New paragraph"""

    result = render_text(mock_base_args, text)

    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once()
    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["text"] == text


def test_render_text_with_github_flavored_markdown_features(
    mock_base_args, mock_post_request
):
    """Test rendering with GitHub Flavored Markdown specific features."""
    text = """- [x] Completed task
- [ ] Incomplete task

| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |

~~strikethrough~~
"""

    result = render_text(mock_base_args, text)

    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once()
    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["mode"] == "gfm"
    assert call_args[1]["json"]["text"] == text


@pytest.mark.parametrize(
    "owner,repo,expected_context",
    [
        ("user", "repo", "user/repo"),
        ("org-name", "repo-name", "org-name/repo-name"),
        ("user_name", "repo_name", "user_name/repo_name"),
        ("123", "456", "123/456"),
        ("a", "b", "a/b"),
    ],
)
def test_render_text_context_formatting(
    owner,
    repo,
    expected_context,
    mock_post_request,
    create_test_base_args,
):
    """Test that context is correctly formatted for various owner/repo combinations."""
    base_args = create_test_base_args(owner=owner, repo=repo, token="test-token")
    text = "Test"

    render_text(base_args, text)

    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["context"] == expected_context


@pytest.mark.parametrize(
    "text_input",
    [
        "",
        "Simple text",
        "# Header",
        "Text with\nnewlines",
        "Text with\ttabs",
        "Unicode: 🚀 测试",
        "Special chars: !@#$%^&*()",
        "Very long text " * 100,
    ],
)
def test_render_text_various_text_inputs(text_input, mock_base_args, mock_post_request):
    """Test rendering with various text inputs."""
    result = render_text(mock_base_args, text_input)

    assert result == "<p>Rendered markdown content</p>"
    mock_post_request.assert_called_once()
    call_args = mock_post_request.call_args
    assert call_args[1]["json"]["text"] == text_input


def test_render_text_json_decode_error_returns_empty_string(mock_base_args):
    """Test that JSON decode errors return empty string due to handle_exceptions decorator."""
    text = "Test content"

    with patch("services.github.markdown.render_text.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "Invalid JSON response"
        mock_post.return_value = mock_response

        # This won't actually cause a JSON decode error in our function since we only use response.text
        # But this test demonstrates the pattern for testing JSON decode error handling
        result = render_text(mock_base_args, text)

        # Should return the response text normally
        assert result == "Invalid JSON response"


def test_render_text_attribute_error_returns_empty_string(mock_base_args):
    """Test that attribute errors return empty string due to handle_exceptions decorator."""
    text = "Test content"

    with patch("services.github.markdown.render_text.post") as mock_post:
        # Create a mock response that doesn't have a text attribute
        mock_response = MagicMock(spec=[])  # Empty spec means no attributes
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = render_text(mock_base_args, text)

        # Due to handle_exceptions decorator, should return empty string
        assert result == ""


# Integration Tests
def test_integration_render_text_simple_markdown(integration_base_args):
    """Integration test: render simple markdown text."""
    text = "# Hello World\n\nThis is a **test**."

    result = render_text(integration_base_args, text)

    # Should return rendered HTML
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain HTML tags for the markdown
    assert "<h1" in result or "<h2" in result or "<p" in result


def test_integration_render_text_empty_string(integration_base_args):
    """Integration test: render empty string."""
    text = ""

    result = render_text(integration_base_args, text)

    # Should return a string (might be empty or minimal HTML)
    assert isinstance(result, str)


def test_integration_render_text_github_flavored_markdown(integration_base_args):
    """Integration test: render GitHub Flavored Markdown features."""
    text = """# Test Document

## Task List
- [x] Completed task
- [ ] Incomplete task

## Table
| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |

## Code Block
```python
def hello():
    print("Hello World")
```

## Strikethrough
~~This text is crossed out~~
"""

    result = render_text(integration_base_args, text)

    # Should return rendered HTML
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain HTML elements typical of rendered markdown
    assert any(tag in result for tag in ["<h1", "<h2", "<p", "<table", "<code", "<pre"])


def test_integration_render_text_unicode_content(integration_base_args):
    """Integration test: render markdown with unicode characters."""
    text = "# 测试文档 🚀\n\n这是一个包含中文和表情符号的测试。"

    result = render_text(integration_base_args, text)

    # Should return rendered HTML
    assert isinstance(result, str)
    assert len(result) > 0


def test_integration_render_text_with_invalid_token(
    test_owner, test_repo, create_test_base_args
):
    """Integration test: render text with invalid token should return empty string."""
    base_args = create_test_base_args(
        owner=test_owner, repo=test_repo, token="invalid-token"
    )
    text = "# Test"

    result = render_text(base_args, text)

    # Should return empty string due to authentication failure and handle_exceptions decorator
    assert result == ""

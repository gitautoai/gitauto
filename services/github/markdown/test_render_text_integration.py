import pytest
from services.github.markdown.render_text import render_text
from services.github.types.github_types import BaseArgs
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def integration_base_args():
    """Fixture providing real BaseArgs for integration testing."""
    return BaseArgs(
        owner=OWNER,
        repo=REPO,
        token=TOKEN
    )


def test_integration_render_text_simple_markdown(integration_base_args):
    """Integration test: render simple markdown text."""
    text = "# Hello World\n\nThis is a **test**."
    
    result = render_text(integration_base_args, text)
    
    # Should return rendered HTML
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain HTML tags for the markdown
    assert "<h1>" in result or "<h2>" in result or "<p>" in result


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
    assert any(tag in result for tag in ["<h1>", "<h2>", "<p>", "<table>", "<code>", "<pre>"])


def test_integration_render_text_unicode_content(integration_base_args):
    """Integration test: render markdown with unicode characters."""
    text = "# 测试文档 🚀\n\n这是一个包含中文和表情符号的测试。"
    
    result = render_text(integration_base_args, text)
    
    # Should return rendered HTML
    assert isinstance(result, str)
    assert len(result) > 0


def test_integration_render_text_with_invalid_token():
    """Integration test: render text with invalid token should return empty string."""
    base_args = BaseArgs(owner=OWNER, repo=REPO, token="invalid-token")
    text = "# Test"
    
    result = render_text(base_args, text)
    
    # Should return empty string due to authentication failure and handle_exceptions decorator
    assert result == ""
import pytest
from utils.extract_urls import extract_image_urls, extract_urls


def test_extract_image_urls_with_valid_images():
    text = """
    <img width="1352" alt="Screenshot 1" src="https://github.com/user-attachments/assets/image1.png" />
    <img height="800" alt="Another image" src="https://example.com/image2.jpg" />
    """
    result = extract_image_urls(text)
    
    assert len(result) == 2
    assert result[0]["alt"] == "Screenshot 1"
    assert result[0]["url"] == "https://github.com/user-attachments/assets/image1.png"
    assert result[1]["alt"] == "Another image"
    assert result[1]["url"] == "https://example.com/image2.jpg"


def test_extract_image_urls_with_svg_images():
    text = """
    <img width="100" alt="SVG Icon" src="https://example.com/icon.svg" />
    <img height="200" alt="PNG Image" src="https://example.com/image.png" />
    """
    result = extract_image_urls(text)
    
    assert len(result) == 1
    assert result[0]["alt"] == "PNG Image"
    assert result[0]["url"] == "https://example.com/image.png"


def test_extract_image_urls_with_no_images():
    text = "This is a text without any images."
    result = extract_image_urls(text)
    
    assert result == []


def test_extract_image_urls_with_exception():
    # Test the exception handling by passing None instead of a string
    result = extract_image_urls(None)
    
    assert result == []


def test_extract_urls_with_github_urls():
    text = """
    Check these GitHub URLs:
    https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py
    https://github.com/user/repo/blob/feature-branch/src/main.py#L10-L20
    https://github.com/org/project/blob/a1b2c3d4e5f6/README.md
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 3
    assert "https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py" in github_urls
    assert "https://github.com/user/repo/blob/feature-branch/src/main.py#L10-L20" in github_urls
    assert "https://github.com/org/project/blob/a1b2c3d4e5f6/README.md" in github_urls
    assert len(other_urls) == 0


def test_extract_urls_with_other_urls():
    text = """
    Check these non-GitHub URLs:
    https://example.com
    http://test.org/page
    https://docs.python.org/3/library/re.html
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 0
    assert len(other_urls) == 3
    assert "https://example.com" in other_urls
    assert "http://test.org/page" in other_urls
    assert "https://docs.python.org/3/library/re.html" in other_urls


def test_extract_urls_with_mixed_urls():
    text = """
    Mixed URLs:
    https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py
    https://example.com
    https://github.com/user/repo/blob/feature-branch/src/main.py
    http://test.org/page
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 2
    assert "https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py" in github_urls
    assert "https://github.com/user/repo/blob/feature-branch/src/main.py" in github_urls
    
    assert len(other_urls) == 2
    assert "https://example.com" in other_urls
    assert "http://test.org/page" in other_urls


def test_extract_urls_with_no_urls():
    text = "This is a text without any URLs."
    github_urls, other_urls = extract_urls(text)
    
    assert github_urls == []
    assert other_urls == []


def test_extract_urls_with_invalid_github_urls():
    text = """
    These look like GitHub URLs but don't match the pattern:
    https://github.com/user/repo/tree/main
    https://github.com/user/repo/issues/123
    https://github.com/user
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 0
    assert len(other_urls) == 3
    assert "https://github.com/user/repo/tree/main" in other_urls
    assert "https://github.com/user/repo/issues/123" in other_urls
    assert "https://github.com/user" in other_urls


def test_extract_urls_with_urls_in_parentheses():
    text = """
    URLs in parentheses (https://github.com/gitautoai/gitauto/blob/main/file.py) and
    (https://example.com) should be extracted.
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 1
    assert "https://github.com/gitautoai/gitauto/blob/main/file.py" in github_urls
    
    assert len(other_urls) == 1
    assert "https://example.com" in other_urls
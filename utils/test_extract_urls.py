import pytest
from utils.extract_urls import extract_image_urls, extract_urls
from tests.constants import OWNER, REPO


def test_extract_image_urls_with_valid_images():
    text = """
    <img width="1352" alt="Screenshot 1" src="https://github.com/user-attachments/assets/image1.png" />
    <img height="800" alt="Another image" src="https://github.com/user-attachments/assets/image2.jpg" />
    """
    result = extract_image_urls(text)
    
    assert len(result) == 2
    assert result[0]["alt"] == "Screenshot 1"
    assert result[0]["url"] == "https://github.com/user-attachments/assets/image1.png"
    assert result[1]["alt"] == "Another image"
    assert result[1]["url"] == "https://github.com/user-attachments/assets/image2.jpg"


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


def test_extract_image_urls_with_empty_string():
    result = extract_image_urls("")
    
    assert result == []


def test_extract_image_urls_with_invalid_input():
    result = extract_image_urls(None)
    
    assert result == []


def test_extract_urls_with_github_urls():
    text = f"""
    Check these GitHub URLs:
    https://github.com/{OWNER}/{REPO}/blob/main/utils/extract_urls.py
    https://github.com/{OWNER}/{REPO}/blob/a1b2c3d4e5f6g7h8i9j0/utils/file_manager.py#L10-L20
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 2
    assert f"https://github.com/{OWNER}/{REPO}/blob/main/utils/extract_urls.py" in github_urls
    assert len(other_urls) == 0


def test_extract_urls_with_other_urls():
    text = """
    Check these non-GitHub URLs:
    https://example.com/page
    http://test.org/resource
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 0
    assert len(other_urls) == 2
    assert "https://example.com/page" in other_urls
    assert "http://test.org/resource" in other_urls


def test_extract_urls_with_mixed_urls():
    text = f"""
    Mixed URLs:
    https://github.com/{OWNER}/{REPO}/blob/main/utils/extract_urls.py
    https://example.com/page
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 1
    assert len(other_urls) == 1
    assert f"https://github.com/{OWNER}/{REPO}/blob/main/utils/extract_urls.py" in github_urls
    assert "https://example.com/page" in other_urls


def test_extract_urls_with_no_urls():
    text = "This text contains no URLs at all."
    github_urls, other_urls = extract_urls(text)
    
    assert github_urls == []
    assert other_urls == []


def test_extract_urls_with_empty_string():
    github_urls, other_urls = extract_urls("")
    
    assert github_urls == []
    assert other_urls == []


def test_extract_urls_with_github_url_variations():
    text = f"""
    Different GitHub URL formats:
    https://github.com/{OWNER}/{REPO}/blob/main/file.py
    https://github.com/{OWNER}/{REPO}/blob/a1b2c3d4/file.py
    https://github.com/{OWNER}/{REPO}/blob/feature-branch/file.py
    https://github.com/{OWNER}/{REPO}/blob/main/path/to/file.py#L10
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 4
    assert len(other_urls) == 0


def test_extract_urls_with_similar_but_invalid_github_urls():
    text = f"""
    These look like GitHub URLs but don't match the pattern:
    https://github.com/{OWNER}/{REPO}/tree/main/utils
    https://github.com/{OWNER}/{REPO}/pull/123
    https://github.com/{OWNER}
    """
    github_urls, other_urls = extract_urls(text)
    
    assert len(github_urls) == 0
    assert len(other_urls) == 3
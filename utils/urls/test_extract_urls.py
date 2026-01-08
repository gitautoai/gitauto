from utils.urls.extract_urls import extract_image_urls, extract_urls


def test_extract_image_urls_with_valid_images():
    text = """
    <img width="1352" alt="Screenshot 1" src="https://example.com/image1.png" />
    <img height="800" alt="Screenshot 2" src="https://example.com/image2.jpg" />
    """
    result = extract_image_urls(text)
    assert len(result) == 2
    assert result[0] == {"alt": "Screenshot 1", "url": "https://example.com/image1.png"}
    assert result[1] == {"alt": "Screenshot 2", "url": "https://example.com/image2.jpg"}


def test_extract_image_urls_with_svg():
    text = """
    <img alt="SVG Image" src="https://example.com/image.svg" />
    <img alt="PNG Image" src="https://example.com/image.png" />
    """
    result = extract_image_urls(text)
    assert len(result) == 1
    assert result[0] == {"alt": "PNG Image", "url": "https://example.com/image.png"}


def test_extract_image_urls_with_invalid_input():
    result = extract_image_urls("")
    assert result == []

    result = extract_image_urls("<img>")
    assert result == []


def test_extract_urls_with_github_urls():
    text = """
    Check these GitHub files:
    https://github.com/owner/repo/blob/main/src/file.py
    https://github.com/owner/repo/blob/a1b2c3d/src/file.py#L10
    https://github.com/owner/repo/blob/feature-branch/src/file.py#L10-L20
    """
    github_urls, other_urls = extract_urls(text)
    assert len(github_urls) == 3
    assert len(other_urls) == 0
    assert "https://github.com/owner/repo/blob/main/src/file.py" in github_urls
    assert "https://github.com/owner/repo/blob/a1b2c3d/src/file.py#L10" in github_urls
    assert (
        "https://github.com/owner/repo/blob/feature-branch/src/file.py#L10-L20"
        in github_urls
    )


def test_extract_urls_with_mixed_urls():
    text = """
    GitHub: https://github.com/owner/repo/blob/main/file.py
    Other: https://example.com
    Another: http://test.com/path
    """
    github_urls, other_urls = extract_urls(text)
    assert len(github_urls) == 1
    assert len(other_urls) == 2
    assert "https://github.com/owner/repo/blob/main/file.py" in github_urls
    assert "https://example.com" in other_urls
    assert "http://test.com/path" in other_urls


def test_extract_urls_with_no_urls():
    text = "This text contains no URLs"
    github_urls, other_urls = extract_urls(text)
    assert len(github_urls) == 0
    assert len(other_urls) == 0


def test_extract_urls_with_invalid_github_urls():
    text = """
    Invalid GitHub URLs:
    https://github.com/owner/repo/blob/
    https://github.com/owner/repo/blob/main/
    https://github.com/owner/repo/tree/main/file.py
    """
    github_urls, other_urls = extract_urls(text)
    assert len(github_urls) == 0
    assert len(other_urls) == 3

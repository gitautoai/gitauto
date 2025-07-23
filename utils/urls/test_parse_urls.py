from tests.constants import OWNER, REPO
from utils.urls.parse_urls import parse_github_url


def test_parse_github_url_basic():
    url = f"https://github.com/{OWNER}/{REPO}/blob/main/utils/urls/parse_urls.py"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_start_line():
    url = f"https://github.com/{OWNER}/{REPO}/blob/main/utils/urls/parse_urls.py#L10"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] is None


def test_parse_github_url_with_line_range():
    url = (
        f"https://github.com/{OWNER}/{REPO}/blob/main/utils/urls/parse_urls.py#L10-L20"
    )
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] == 20


def test_parse_github_url_with_commit_hash():
    url = (
        f"https://github.com/{OWNER}/{REPO}/blob/a1b2c3d4e5f6/utils/urls/parse_urls.py"
    )
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "a1b2c3d4e5f6"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_feature_branch():
    url = f"https://github.com/{OWNER}/{REPO}/blob/feature-branch/utils/urls/parse_urls.py"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "feature-branch"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_nested_path():
    url = f"https://github.com/{OWNER}/{REPO}/blob/main/deeply/nested/path/to/file.py"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "deeply/nested/path/to/file.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_empty_line_number():
    url = f"https://github.com/{OWNER}/{REPO}/blob/main/utils/urls/parse_urls.py#L"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_empty_end_line():
    url = f"https://github.com/{OWNER}/{REPO}/blob/main/utils/urls/parse_urls.py#L10-L"
    result = parse_github_url(url)

    assert result["owner"] == OWNER
    assert result["repo"] == REPO
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] is None

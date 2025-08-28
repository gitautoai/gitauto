from utils.urls.parse_urls import parse_github_url


def test_parse_github_url_basic(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/utils/urls/parse_urls.py"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_start_line(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/utils/urls/parse_urls.py#L10"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] is None


def test_parse_github_url_with_line_range(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/utils/urls/parse_urls.py#L10-L20"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] == 20


def test_parse_github_url_with_commit_hash(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/a1b2c3d4e5f6/utils/urls/parse_urls.py"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "a1b2c3d4e5f6"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_feature_branch(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/feature-branch/utils/urls/parse_urls.py"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "feature-branch"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_nested_path(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/deeply/nested/path/to/file.py"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "deeply/nested/path/to/file.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_empty_line_number(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/utils/urls/parse_urls.py#L"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] is None
    assert result["end_line"] is None


def test_parse_github_url_with_empty_end_line(test_owner, test_repo):
    url = f"https://github.com/{test_owner}/{test_repo}/blob/main/utils/urls/parse_urls.py#L10-L"
    result = parse_github_url(url)

    assert result["owner"] == test_owner
    assert result["repo"] == test_repo
    assert result["ref"] == "main"
    assert result["file_path"] == "utils/urls/parse_urls.py"
    assert result["start_line"] == 10
    assert result["end_line"] is None

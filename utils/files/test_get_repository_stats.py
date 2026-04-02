import os

import pytest

from utils.files.get_repository_stats import (
    DEFAULT_REPO_STATS,
    get_repository_stats,
)

# Real git repositories for sociable tests
GITAUTO_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEBSITE_REPO = os.path.abspath(os.path.join(GITAUTO_REPO, "..", "website"))


@pytest.mark.integration
def test_get_repository_stats_on_gitauto_repo():
    result = get_repository_stats(local_path=GITAUTO_REPO)
    assert result["file_count"] > 500
    assert result["code_lines"] > 100000


@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.isdir(os.path.join(WEBSITE_REPO, ".git")),
    reason="website repo clone not available",
)
def test_get_repository_stats_on_website_repo():
    result = get_repository_stats(local_path=WEBSITE_REPO)
    assert result["file_count"] > 500
    assert result["code_lines"] > 10000


def test_get_repository_stats_nonexistent_path():
    result = get_repository_stats(local_path="/nonexistent/path")
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_not_a_git_repo(tmp_path):
    result = get_repository_stats(local_path=str(tmp_path))
    assert result == DEFAULT_REPO_STATS


@pytest.mark.integration
def test_get_repository_stats_empty_repo(tmp_path):
    """Empty git repo with no commits returns default stats."""
    repo_dir = str(tmp_path / "empty-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")
    result = get_repository_stats(local_path=repo_dir)
    assert result == DEFAULT_REPO_STATS


@pytest.mark.integration
def test_get_repository_stats_repo_with_known_files(tmp_path):
    """Create a repo with exactly 3 files, 5 total lines, and verify."""
    repo_dir = str(tmp_path / "test-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    # a.py: 2 lines, b.js: 2 lines, c.txt: 1 line = 5 total
    with open(os.path.join(repo_dir, "a.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\ny = 2\n")
    with open(os.path.join(repo_dir, "b.js"), "w", encoding="utf-8") as f:
        f.write("const a = 1;\nconst b = 2;\n")
    with open(os.path.join(repo_dir, "c.txt"), "w", encoding="utf-8") as f:
        f.write("hello\n")

    os.system(
        f"cd {repo_dir} && git add . && git commit -m init --quiet --author='Test <t@t.com>'"
    )

    result = get_repository_stats(local_path=repo_dir)
    assert result == {
        "file_count": 3,
        "code_lines": 5,
    }

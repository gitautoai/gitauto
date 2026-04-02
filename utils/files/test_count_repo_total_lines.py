import os

import pytest

from utils.files.count_repo_total_lines import count_repo_total_lines

GITAUTO_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEBSITE_REPO = os.path.abspath(os.path.join(GITAUTO_REPO, "..", "website"))


# Sociable tests — real repos
@pytest.mark.integration
def test_count_repo_total_lines_gitauto():
    assert count_repo_total_lines(local_path=GITAUTO_REPO) > 100000


@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.isdir(os.path.join(WEBSITE_REPO, ".git")),
    reason="website repo clone not available",
)
def test_count_repo_total_lines_website():
    assert count_repo_total_lines(local_path=WEBSITE_REPO) > 10000


# Solitary tests — isolated tmp repos
def test_count_repo_total_lines_nonexistent_path():
    assert count_repo_total_lines(local_path="/nonexistent/path") == 0


def test_count_repo_total_lines_not_a_git_repo(tmp_path):
    assert count_repo_total_lines(local_path=str(tmp_path)) == 0


@pytest.mark.integration
def test_count_repo_total_lines_empty_repo(tmp_path):
    repo_dir = str(tmp_path / "empty-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")
    assert count_repo_total_lines(local_path=repo_dir) == 0


@pytest.mark.integration
def test_count_repo_total_lines_exact_count(tmp_path):
    repo_dir = str(tmp_path / "test-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    # 2 + 2 + 1 = 5 lines
    with open(os.path.join(repo_dir, "a.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\ny = 2\n")
    with open(os.path.join(repo_dir, "b.js"), "w", encoding="utf-8") as f:
        f.write("const a = 1;\nconst b = 2;\n")
    with open(os.path.join(repo_dir, "c.txt"), "w", encoding="utf-8") as f:
        f.write("hello\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )
    assert count_repo_total_lines(local_path=repo_dir) == 5

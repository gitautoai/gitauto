import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from utils.files.count_repo_total_files import count_repo_total_files

GITAUTO_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEBSITE_REPO = os.path.abspath(os.path.join(GITAUTO_REPO, "..", "website"))


# Sociable tests — real repos
@pytest.mark.integration
def test_count_repo_total_files_gitauto():
    assert count_repo_total_files(local_path=GITAUTO_REPO) > 500


@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.isdir(os.path.join(WEBSITE_REPO, ".git")),
    reason="website repo clone not available",
)
def test_count_repo_total_files_website():
    assert count_repo_total_files(local_path=WEBSITE_REPO) > 500


# Solitary tests — isolated tmp repos
def test_count_repo_total_files_nonexistent_path():
    # Nonexistent path triggers ValueError in run_subprocess, caught by handle_exceptions → 0
    assert count_repo_total_files(local_path="/nonexistent/path") == 0


def test_count_repo_total_files_not_a_git_repo(tmp_path):
    # A directory without .git triggers git error, caught by handle_exceptions → 0
    assert count_repo_total_files(local_path=str(tmp_path)) == 0


@pytest.mark.integration
def test_count_repo_total_files_empty_repo(tmp_path):
    # Empty repo with no commits means HEAD doesn't exist → empty output → 0
    repo_dir = str(tmp_path / "empty-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")
    assert count_repo_total_files(local_path=repo_dir) == 0


@pytest.mark.integration
def test_count_repo_total_files_exact_count(tmp_path):
    # Verify exact file count matches committed files
    repo_dir = str(tmp_path / "test-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    for name in ["a.py", "b.js", "c.txt"]:
        with open(os.path.join(repo_dir, name), "w", encoding="utf-8") as f:
            f.write("content\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )
    assert count_repo_total_files(local_path=repo_dir) == 3


@pytest.mark.integration
def test_count_repo_total_files_single_file(tmp_path):
    # Boundary: exactly one file should return 1, not 0 or 2
    repo_dir = str(tmp_path / "single-file-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    with open(os.path.join(repo_dir, "only.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )
    assert count_repo_total_files(local_path=repo_dir) == 1


@pytest.mark.integration
def test_count_repo_total_files_nested_directories(tmp_path):
    # Files in subdirectories should all be counted by git ls-tree -r
    repo_dir = str(tmp_path / "nested-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    os.makedirs(os.path.join(repo_dir, "src", "utils"), exist_ok=True)
    files = ["README.md", "src/main.py", "src/utils/helper.py", "src/utils/config.json"]
    for name in files:
        with open(os.path.join(repo_dir, name), "w", encoding="utf-8") as f:
            f.write("content\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )
    assert count_repo_total_files(local_path=repo_dir) == 4


@pytest.mark.integration
def test_count_repo_total_files_unicode_filenames(tmp_path):
    # Unicode filenames should be counted correctly by git
    repo_dir = str(tmp_path / "unicode-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    for name in ["café.py", "日本語.txt", "normal.js"]:
        with open(os.path.join(repo_dir, name), "w", encoding="utf-8") as f:
            f.write("content\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )
    assert count_repo_total_files(local_path=repo_dir) == 3


@pytest.mark.integration
def test_count_repo_total_files_untracked_files_not_counted(tmp_path):
    # Only committed files should be counted; untracked files should be ignored
    repo_dir = str(tmp_path / "untracked-repo")
    os.makedirs(repo_dir)
    os.system(f"git init {repo_dir} --quiet")

    with open(os.path.join(repo_dir, "committed.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\n")

    os.system(
        f"cd {repo_dir} && git add . && git -c user.name=Test -c user.email=t@t.com commit -m init --quiet"
    )

    with open(os.path.join(repo_dir, "untracked.py"), "w", encoding="utf-8") as f:
        f.write("y = 2\n")

    assert count_repo_total_files(local_path=repo_dir) == 1


# Mocked tests — exercise specific branches in the function body
def test_count_repo_total_files_run_subprocess_returns_none():
    # When run_subprocess returns None, line 13 takes the else branch → empty string → 0
    with patch(
        "utils.files.count_repo_total_files.run_subprocess", return_value=None
    ):
        assert count_repo_total_files(local_path="/any/path") == 0


def test_count_repo_total_files_stdout_is_none():
    # When result.stdout is None, line 13 takes the else branch → empty string → 0
    mock_result = SimpleNamespace(stdout=None, returncode=0)
    with patch(
        "utils.files.count_repo_total_files.run_subprocess", return_value=mock_result
    ):
        assert count_repo_total_files(local_path="/any/path") == 0


def test_count_repo_total_files_stdout_is_whitespace_only():
    # When stdout is only whitespace, strip() produces "" → return 0
    mock_result = SimpleNamespace(stdout="   \n\n  ", returncode=0)
    with patch(
        "utils.files.count_repo_total_files.run_subprocess", return_value=mock_result
    ):
        assert count_repo_total_files(local_path="/any/path") == 0


def test_count_repo_total_files_run_subprocess_raises_exception():
    # When run_subprocess raises, handle_exceptions catches it and returns default 0
    with patch(
        "utils.files.count_repo_total_files.run_subprocess",
        side_effect=ValueError("Command failed"),
    ):
        assert count_repo_total_files(local_path="/any/path") == 0


def test_count_repo_total_files_run_subprocess_called_with_correct_args():
    # Verify the correct git command and cwd are passed to run_subprocess
    mock_result = SimpleNamespace(stdout="file1.py\nfile2.py\n", returncode=0)
    with patch(
        "utils.files.count_repo_total_files.run_subprocess", return_value=mock_result
    ) as mock_run:
        result = count_repo_total_files(local_path="/my/repo")
        mock_run.assert_called_once_with(
            args=["git", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd="/my/repo",
        )
        # Also verify the count is correct for 2 files
        assert result == 2


def test_count_repo_total_files_stdout_trailing_newline():
    # git ls-tree output typically ends with \n; strip() should prevent an extra empty count
    mock_result = SimpleNamespace(stdout="a.py\nb.py\nc.py\n", returncode=0)
    with patch(
        "utils.files.count_repo_total_files.run_subprocess", return_value=mock_result
    ):
        assert count_repo_total_files(local_path="/any/path") == 3


def test_count_repo_total_files_empty_string_path():
    # Empty string path should be handled gracefully → 0
    assert count_repo_total_files(local_path="") == 0

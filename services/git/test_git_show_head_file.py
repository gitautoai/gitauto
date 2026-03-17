import os
from unittest.mock import patch

import pytest

from services.git.git_show_head_file import git_show_head_file


def test_returns_file_content():
    with patch("services.git.git_show_head_file.run_subprocess") as mock_run:
        mock_run.return_value.stdout = "file content\n"
        result = git_show_head_file(file_path="src/main.py", clone_dir="/tmp/repo")
        assert result == "file content\n"
        mock_run.assert_called_once_with(
            args=["git", "show", "HEAD:src/main.py"], cwd="/tmp/repo"
        )


def test_returns_none_for_new_file():
    with patch("services.git.git_show_head_file.run_subprocess") as mock_run:
        mock_run.side_effect = ValueError(
            "Command failed: fatal: path 'new.py' does not exist"
        )
        result = git_show_head_file(file_path="new.py", clone_dir="/tmp/repo")
        assert result is None


@pytest.mark.integration
def test_returns_committed_content(local_repo):
    _, work_dir = local_repo
    result = git_show_head_file(file_path="README.md", clone_dir=work_dir)
    assert result == "# Test\n"


@pytest.mark.integration
def test_returns_committed_content_not_disk_content(local_repo):
    """Verify git_show_head_file returns the committed version, not the disk version."""
    _, work_dir = local_repo
    # Modify the file on disk without committing
    readme_path = os.path.join(work_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Modified on disk\n")

    result = git_show_head_file(file_path="README.md", clone_dir=work_dir)
    # Should return the committed version, not the disk version
    assert result == "# Test\n"


@pytest.mark.integration
def test_returns_none_for_nonexistent_file(local_repo):
    _, work_dir = local_repo
    result = git_show_head_file(file_path="nonexistent.py", clone_dir=work_dir)
    assert result is None

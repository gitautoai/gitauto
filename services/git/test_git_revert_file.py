# pyright: reportUnusedVariable=false
# pylint: disable=unused-argument
import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_revert_file import git_revert_file


@patch("services.git.git_revert_file.read_local_file", return_value="reverted content")
@patch("services.git.git_revert_file.git_commit_and_push")
@patch("services.git.git_revert_file.run_subprocess")
def test_falls_back_to_base_branch_without_commit_sha(
    mock_subprocess, mock_commit, _mock_read, create_test_base_args
):
    """Without latest_commit_sha (new_pr_handler), reverts to base_branch."""
    base_args = create_test_base_args(
        clone_dir="/tmp/test-repo",
        latest_commit_sha="",
    )
    result = git_revert_file(file_path="test/index.test.tsx", base_args=base_args)

    assert result.success is True
    assert "Reverted test/index.test.tsx to main" == result.message
    assert result.content == "reverted content"
    mock_subprocess.assert_called_once_with(
        ["git", "checkout", "main", "--", "test/index.test.tsx"],
        "/tmp/test-repo",
    )
    mock_commit.assert_called_once_with(
        base_args=base_args,
        message="Revert test/index.test.tsx to main",
        files=["test/index.test.tsx"],
    )


@patch("services.git.git_revert_file.read_local_file", return_value="sha content")
@patch("services.git.git_revert_file.git_commit_and_push")
@patch("services.git.git_revert_file.run_subprocess")
def test_uses_latest_commit_sha_when_available(
    mock_subprocess, _mock_commit, _mock_read, create_test_base_args
):
    """With latest_commit_sha (check_suite/review handlers), reverts to that SHA."""
    base_args = create_test_base_args(
        clone_dir="/tmp/test-repo",
        latest_commit_sha="abc123def456",
    )

    result = git_revert_file(file_path="src/app.ts", base_args=base_args)

    assert result.success is True
    assert (
        result.message
        == "Reverted src/app.ts to the version before agent started (abc123d)"
    )
    assert result.content == "sha content"
    mock_subprocess.assert_called_once_with(
        ["git", "checkout", "abc123def456", "--", "src/app.ts"],
        "/tmp/test-repo",
    )


@patch("services.git.git_revert_file.read_local_file", return_value="unchanged content")
@patch(
    "services.git.git_revert_file.run_subprocess",
    side_effect=ValueError("git checkout failed"),
)
def test_returns_current_content_on_failure(
    _mock_subprocess, _mock_read, create_test_base_args
):
    """On failure, returns current file content so agent knows what it's working with."""
    base_args = create_test_base_args(
        clone_dir="/tmp/test-repo",
        latest_commit_sha="",
    )
    result = git_revert_file(file_path="src/broken.ts", base_args=base_args)

    assert result.success is False
    assert result.file_path == "src/broken.ts"
    assert result.content == "unchanged content"


@pytest.mark.integration
def test_git_revert_file_falls_back_to_base(local_repo, create_test_base_args):
    """Sociable (new_pr case): no latest_commit_sha, reverts to base_branch."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        readme_path = os.path.join(clone_dir, "README.md")
        with open(readme_path, encoding="utf-8") as f:
            original = f.read()

        # Create feature branch and modify README (simulates agent creating PR)
        subprocess.run(
            ["git", "checkout", "-b", "feature/revert-test"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Modified\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@test.com",
                "commit",
                "-m",
                "modify readme",
            ],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:refs/heads/feature/revert-test"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/revert-test",
            base_branch="main",
            latest_commit_sha="",
        )

        result = git_revert_file(file_path="README.md", base_args=base_args)

        assert result.success is True
        assert "Reverted README.md to main" == result.message
        assert result.content == original
        with open(readme_path, encoding="utf-8") as f:
            assert f.read() == original


@pytest.mark.integration
def test_git_revert_file_uses_commit_sha(local_repo, create_test_base_args):
    """Sociable (check_suite case): latest_commit_sha set, reverts to that SHA."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        # Create feature branch with PR author's change
        subprocess.run(
            ["git", "checkout", "-b", "feature/revert-sha"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        readme_path = os.path.join(clone_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# PR author change\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@test.com",
                "commit",
                "-m",
                "PR author change",
            ],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        # This SHA is the "before agent started" point
        pr_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        subprocess.run(
            ["git", "push", "origin", "HEAD:refs/heads/feature/revert-sha"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )

        # Agent modifies the file further
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Agent broke this\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@test.com",
                "commit",
                "-m",
                "agent change",
            ],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:refs/heads/feature/revert-sha"],
            cwd=clone_dir,
            check=True,
            capture_output=True,
        )

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/revert-sha",
            base_branch="main",
            latest_commit_sha=pr_sha,
        )

        result = git_revert_file(file_path="README.md", base_args=base_args)

        assert result.success is True
        assert (
            result.message
            == f"Reverted README.md to the version before agent started ({pr_sha[:7]})"
        )
        assert result.content == "# PR author change\n"
        with open(readme_path, encoding="utf-8") as f:
            assert f.read() == "# PR author change\n"

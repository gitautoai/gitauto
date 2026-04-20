# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git import apply_diff_to_file as apply_diff_to_file_mod
from services.git.apply_diff_to_file import apply_diff_to_file
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import GitCommitResult
from utils.files.apply_patch import PatchResult


def _ok_commit(**_kwargs):
    return GitCommitResult(success=True)


def test_successful_file_update(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("print('hello world')\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(
            content="print('hello modified world')\n", error=""
        )

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-print('hello world')\n+print('hello modified world')",
            file_path="test.py",
            base_args=base_args,
        )

        assert result.success is True
        assert result.message == "Updated test.py."
        assert (tmp_path / "test.py").read_text() == "print('hello modified world')\n"


def test_new_file_creation(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content="print('new file')\n", error="")

        result = apply_diff_to_file(
            diff="--- /dev/null\n+++ new_file.py\n@@ -0,0 +1 @@\n+print('new file')",
            file_path="new_file.py",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert (tmp_path / "new_file.py").read_text() == "print('new file')\n"


def test_deletion_diff(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "to_delete.py").write_text("# delete me\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content="", error="")

        result = apply_diff_to_file(
            diff="--- to_delete.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-# delete me",
            file_path="to_delete.py",
            base_args=base_args,
        )

        assert result.success is True
        assert result.message == "Deleted to_delete.py."
        assert not (tmp_path / "to_delete.py").exists()


def test_directory_path_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "my_dir").mkdir()

    result = apply_diff_to_file(
        diff="--- my_dir\n+++ my_dir\n@@ -1 +1 @@\n-old\n+new",
        file_path="my_dir",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="'my_dir' is a directory, not a file.",
        file_path="my_dir",
        content="",
    )


def test_patch_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("original\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content="", error="Failed to apply diff.")

        result = apply_diff_to_file(
            diff="invalid diff",
            file_path="test.py",
            base_args=base_args,
        )

        assert result == FileWriteResult(
            success=False,
            message="Failed to apply diff.",
            file_path="test.py",
            content="original\n",
        )


def test_no_changes_returns_success_false(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    original_content = "print('hello world')\n"
    (tmp_path / "test.py").write_text(original_content)

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content=original_content, error="")

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="test.py",
            base_args=base_args,
        )

        assert result == FileWriteResult(
            success=False,
            message="No changes to test.py.",
            file_path="test.py",
            content="print('hello world')\n",
        )


def test_reads_disk_version_not_committed_version(create_test_base_args, tmp_path):
    """Verify we read from disk (which formatters may have modified), not git HEAD.
    Claude reads the disk version, so diffs must be applied against it."""
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    # Disk has Prettier-formatted content (what Claude sees)
    (tmp_path / "test.py").write_text("formatted content\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(
            content="formatted and modified content\n", error=""
        )

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-formatted content\n+formatted and modified content",
            file_path="test.py",
            base_args=base_args,
        )

        # apply_patch should receive the disk content as original_text
        mock_patch.assert_called_once()
        call_kwargs = mock_patch.call_args
        assert call_kwargs[1]["original_text"] == "formatted content\n"

        assert result.success is True
        assert result.message == "Updated test.py."


def test_extra_kwargs_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content="new\n", error="")

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="test.py",
            base_args=base_args,
            extra_param="ignored",
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True


def test_nested_file_path(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    nested_dir = tmp_path / "src" / "utils"
    nested_dir.mkdir(parents=True)
    (nested_dir / "helper.py").write_text("old\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch, patch(
        "services.git.apply_diff_to_file.git_commit_and_push", side_effect=_ok_commit
    ):
        mock_patch.return_value = PatchResult(content="new\n", error="")

        result = apply_diff_to_file(
            diff="--- src/utils/helper.py\n+++ src/utils/helper.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="src/utils/helper.py",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert (nested_dir / "helper.py").read_text() == "new\n"


@pytest.mark.integration
def test_apply_diff_end_to_end(local_repo, create_test_base_args):
    """Sociable: apply diff to README, verify pushed to bare repo."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/diff-test",
        )

        diff = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-# Test\n+# Diff Applied"

        result = apply_diff_to_file(
            diff=diff,
            file_path="README.md",
            base_args=base_args,
        )

        assert result.success is True
        assert result.message == "Updated README.md."

        with open(os.path.join(clone_dir, "README.md"), encoding="utf-8") as f:
            readme_content = f.read()
        assert readme_content.count("# Diff Applied") == 1

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--format=%s", "feature/diff-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert log.stdout.strip().splitlines()[0] == "Update README.md"


def test_apply_diff_to_file_propagates_concurrent_push(
    create_test_base_args, tmp_path, monkeypatch
):
    """Concurrent push from git_commit_and_push must bubble up as FileWriteResult(concurrent_push_detected=True) so chat_with_agent breaks the agent loop instead of retrying futilely."""
    (tmp_path / "a.py").write_text("old\n")

    monkeypatch.setattr(
        apply_diff_to_file_mod,
        "git_commit_and_push",
        lambda **kwargs: GitCommitResult(success=False, concurrent_push_detected=True),
    )
    monkeypatch.setattr(
        apply_diff_to_file_mod,
        "apply_patch",
        lambda **kwargs: PatchResult(content="new\n", error=""),
    )

    base_args = create_test_base_args(
        skip_ci=False, clone_dir=str(tmp_path), new_branch="feature/raced"
    )
    diff = "--- a/a.py\n+++ b/a.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    result = apply_diff_to_file(diff=diff, file_path="a.py", base_args=base_args)

    assert result == FileWriteResult(
        success=False,
        message="Concurrent push detected on `feature/raced` while committing a.py. Another commit landed; aborting this edit.",
        file_path="a.py",
        content="",
        concurrent_push_detected=True,
    )

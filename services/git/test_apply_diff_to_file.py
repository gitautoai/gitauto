# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git.apply_diff_to_file import apply_diff_to_file
from services.github.types.github_types import BaseArgs
from utils.files.apply_patch import PatchResult


@pytest.fixture
def sample_base_args(tmp_path):
    return cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "new_branch": "test_branch",
            "skip_ci": False,
            "clone_dir": str(tmp_path),
        },
    )


def test_successful_file_update(sample_base_args, tmp_path):
    # Create existing file
    (tmp_path / "test.py").write_text("print('hello world')\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(
            content="print('hello modified world')\n", error=""
        )

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-print('hello world')\n+print('hello modified world')",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert "Updated test.py" in result.message
        assert (tmp_path / "test.py").read_text() == "print('hello modified world')\n"


def test_new_file_creation(sample_base_args, tmp_path):
    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content="print('new file')\n", error="")

        result = apply_diff_to_file(
            diff="--- /dev/null\n+++ new_file.py\n@@ -0,0 +1 @@\n+print('new file')",
            file_path="new_file.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert (tmp_path / "new_file.py").read_text() == "print('new file')\n"


def test_deletion_diff(sample_base_args, tmp_path):
    (tmp_path / "to_delete.py").write_text("# delete me\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content="", error="")

        result = apply_diff_to_file(
            diff="--- to_delete.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-# delete me",
            file_path="to_delete.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert "Deleted" in result.message
        assert not (tmp_path / "to_delete.py").exists()


def test_directory_path_error(sample_base_args, tmp_path):
    (tmp_path / "my_dir").mkdir()

    result = apply_diff_to_file(
        diff="--- my_dir\n+++ my_dir\n@@ -1 +1 @@\n-old\n+new",
        file_path="my_dir",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "directory" in result.message


def test_patch_error(sample_base_args, tmp_path):
    (tmp_path / "test.py").write_text("original\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content="", error="Failed to apply diff.")

        result = apply_diff_to_file(
            diff="invalid diff",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "Failed to apply diff" in result.message


def test_no_changes_returns_success_false(sample_base_args, tmp_path):
    original_content = "print('hello world')\n"
    (tmp_path / "test.py").write_text(original_content)

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content=original_content, error="")

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is False
        assert "No changes" in result.message


def test_extra_kwargs_ignored(sample_base_args, tmp_path):
    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content="new\n", error="")

        result = apply_diff_to_file(
            diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="test.py",
            base_args=sample_base_args,
            extra_param="ignored",
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True


def test_nested_file_path(sample_base_args, tmp_path):
    nested_dir = tmp_path / "src" / "utils"
    nested_dir.mkdir(parents=True)
    (nested_dir / "helper.py").write_text("old\n")

    with patch("services.git.apply_diff_to_file.apply_patch") as mock_patch:
        mock_patch.return_value = PatchResult(content="new\n", error="")

        result = apply_diff_to_file(
            diff="--- src/utils/helper.py\n+++ src/utils/helper.py\n@@ -1 +1 @@\n-old\n+new",
            file_path="src/utils/helper.py",
            base_args=sample_base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert (nested_dir / "helper.py").read_text() == "new\n"

# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git.write_and_commit_file import (
    WRITE_AND_COMMIT_FILE,
    write_and_commit_file,
)
from services.types.base_args import BaseArgs


@pytest.fixture
def sample_base_args(tmp_path):
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "test-branch",
            "skip_ci": False,
            "clone_dir": str(tmp_path),
        },
    )


def test_replace_creates_new_file(sample_base_args, tmp_path):
    with patch(
        "services.git.write_and_commit_file.git_show_head_file", return_value=None
    ):
        result = write_and_commit_file(
            file_content="print('hello')",
            file_path="src/test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Created" in result.message

    local_path = tmp_path / "src" / "test.py"
    assert local_path.exists()
    assert local_path.read_text() == "print('hello')\n"


def test_replace_existing_file(sample_base_args, tmp_path):
    # Create existing file on disk so os.path.exists returns True
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("old content\n")

    with patch(
        "services.git.write_and_commit_file.git_show_head_file",
        return_value="old content\n",
    ):
        result = write_and_commit_file(
            file_content="new content",
            file_path="src/test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Updated" in result.message
    assert (file_dir / "test.py").read_text() == "new content\n"


def test_skip_when_content_identical(sample_base_args, tmp_path):
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("same content\n")

    with patch(
        "services.git.write_and_commit_file.git_show_head_file",
        return_value="same content\n",
    ):
        result = write_and_commit_file(
            file_content="same content\n",
            file_path="src/test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_detects_changes_when_disk_modified_by_formatter(sample_base_args, tmp_path):
    """When a formatter modifies the file on disk, we should still detect changes
    because we compare against git HEAD (committed version), not disk."""
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    # Disk has formatter-modified content
    (file_dir / "test.py").write_text("formatted content\n")

    # But git HEAD has the original committed content
    with patch(
        "services.git.write_and_commit_file.git_show_head_file",
        return_value="original content\n",
    ):
        result = write_and_commit_file(
            file_content="formatted content",
            file_path="src/test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Updated" in result.message


def test_directory_path_error(sample_base_args, tmp_path):
    dir_path = tmp_path / "src"
    dir_path.mkdir()

    result = write_and_commit_file(
        file_content="content",
        file_path="src",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "directory" in result.message


def test_preserve_crlf_line_endings(sample_base_args, tmp_path):
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.ts").write_text("line1\r\nline2\r\n")

    with patch(
        "services.git.write_and_commit_file.git_show_head_file",
        return_value="line1\r\nline2\r\n",
    ):
        result = write_and_commit_file(
            file_content="line1\nline2_modified\n",
            file_path="src/test.ts",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    with open(file_dir / "test.ts", "r", encoding="utf-8", newline="") as f:
        assert f.read() == "line1\r\nline2_modified\r\n"


def test_skip_when_content_identical_after_crlf_conversion(sample_base_args, tmp_path):
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.ts").write_text("line1\r\nline2\r\n")

    with patch(
        "services.git.write_and_commit_file.git_show_head_file",
        return_value="line1\r\nline2\r\n",
    ):
        result = write_and_commit_file(
            file_content="line1\nline2\n",
            file_path="src/test.ts",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_ensures_final_newline(sample_base_args, tmp_path):
    with patch(
        "services.git.write_and_commit_file.git_show_head_file", return_value=None
    ):
        result = write_and_commit_file(
            file_content="no trailing newline",
            file_path="test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text().endswith("\n")


def test_extra_kwargs_ignored(sample_base_args, tmp_path):
    with patch(
        "services.git.write_and_commit_file.git_show_head_file", return_value=None
    ):
        result = write_and_commit_file(
            file_content="content",
            file_path="test.py",
            base_args=sample_base_args,
            extra_param="should_be_ignored",
            another_param=123,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True


def test_nested_file_path(sample_base_args, tmp_path):
    with patch(
        "services.git.write_and_commit_file.git_show_head_file", return_value=None
    ):
        result = write_and_commit_file(
            file_content="# deep file",
            file_path="src/utils/helpers/deep/nested/file.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "src/utils/helpers/deep/nested/file.py").exists()


def test_unicode_content(sample_base_args, tmp_path):
    with patch(
        "services.git.write_and_commit_file.git_show_head_file", return_value=None
    ):
        result = write_and_commit_file(
            file_content="print('Hello 世界! 🌍 émojis')",
            file_path="test.py",
            base_args=sample_base_args,
        )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "🌍" in (tmp_path / "test.py").read_text()


def test_tool_definition_structure():
    assert WRITE_AND_COMMIT_FILE["name"] == "write_and_commit_file"
    assert "description" in WRITE_AND_COMMIT_FILE
    assert "input_schema" in WRITE_AND_COMMIT_FILE
    assert WRITE_AND_COMMIT_FILE.get("strict") is True

    params = WRITE_AND_COMMIT_FILE["input_schema"]
    if isinstance(params, dict):
        assert params.get("type") == "object"
        properties = params.get("properties", {})
        if isinstance(properties, dict):
            assert "file_path" in properties
            assert "file_content" in properties
        assert params.get("required") == ["file_path", "file_content"]
        assert params.get("additionalProperties") is False

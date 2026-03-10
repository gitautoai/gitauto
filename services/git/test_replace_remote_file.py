# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git.replace_remote_file import (
    REPLACE_REMOTE_FILE_CONTENT,
    replace_remote_file_content,
)
from services.github.types.github_types import BaseArgs


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
    result = replace_remote_file_content(
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
    # Create existing file
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("old content\n")

    result = replace_remote_file_content(
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

    result = replace_remote_file_content(
        file_content="same content\n",
        file_path="src/test.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_directory_path_error(sample_base_args, tmp_path):
    dir_path = tmp_path / "src"
    dir_path.mkdir()

    result = replace_remote_file_content(
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

    result = replace_remote_file_content(
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

    result = replace_remote_file_content(
        file_content="line1\nline2\n",
        file_path="src/test.ts",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_ensures_final_newline(sample_base_args, tmp_path):
    result = replace_remote_file_content(
        file_content="no trailing newline",
        file_path="test.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text().endswith("\n")


def test_extra_kwargs_ignored(sample_base_args, tmp_path):
    result = replace_remote_file_content(
        file_content="content",
        file_path="test.py",
        base_args=sample_base_args,
        extra_param="should_be_ignored",
        another_param=123,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True


def test_nested_file_path(sample_base_args, tmp_path):
    result = replace_remote_file_content(
        file_content="# deep file",
        file_path="src/utils/helpers/deep/nested/file.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "src/utils/helpers/deep/nested/file.py").exists()


def test_unicode_content(sample_base_args, tmp_path):
    result = replace_remote_file_content(
        file_content="print('Hello 世界! 🌍 émojis')",
        file_path="test.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "🌍" in (tmp_path / "test.py").read_text()


def test_tool_definition_structure():
    assert REPLACE_REMOTE_FILE_CONTENT["name"] == "replace_remote_file_content"
    assert "description" in REPLACE_REMOTE_FILE_CONTENT
    assert "input_schema" in REPLACE_REMOTE_FILE_CONTENT
    assert REPLACE_REMOTE_FILE_CONTENT.get("strict") is True

    params = REPLACE_REMOTE_FILE_CONTENT["input_schema"]
    if isinstance(params, dict):
        assert params.get("type") == "object"
        properties = params.get("properties", {})
        if isinstance(properties, dict):
            assert "file_path" in properties
            assert "file_content" in properties
        assert params.get("required") == ["file_path", "file_content"]
        assert params.get("additionalProperties") is False

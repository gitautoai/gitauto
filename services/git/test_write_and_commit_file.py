# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from typing import cast

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git.git_clone_to_tmp import git_clone_to_tmp
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
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("old content\n")

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

    result = write_and_commit_file(
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

    result = write_and_commit_file(
        file_content="line1\nline2\n",
        file_path="src/test.ts",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_ensures_final_newline(sample_base_args, tmp_path):
    result = write_and_commit_file(
        file_content="no trailing newline",
        file_path="test.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text().endswith("\n")


def test_extra_kwargs_ignored(sample_base_args, tmp_path):
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
    result = write_and_commit_file(
        file_content="# deep file",
        file_path="src/utils/helpers/deep/nested/file.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "src/utils/helpers/deep/nested/file.py").exists()


def test_unicode_content(sample_base_args, tmp_path):
    result = write_and_commit_file(
        file_content="print('Hello 世界! 🌍 émojis')",
        file_path="test.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "🌍" in (tmp_path / "test.py").read_text()


def test_diff_included_for_existing_file(sample_base_args, tmp_path):
    """When updating an existing file, the result message should include the unified diff."""
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    original = "\n".join(f"line {i}" for i in range(20)) + "\n"
    (file_dir / "big.py").write_text(original)

    new_content = "\n".join(f"replaced {i}" for i in range(15)) + "\n"
    result = write_and_commit_file(
        file_content=new_content,
        file_path="src/big.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Diff:" not in result.message
    assert "-line " in result.diff
    assert "+replaced " in result.diff


def test_diff_included_for_small_change(sample_base_args, tmp_path):
    """Even small changes should include the diff."""
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    lines = [f"line {i}" for i in range(20)]
    original = "\n".join(lines) + "\n"
    (file_dir / "small.py").write_text(original)

    lines[5] = "modified line 5"
    new_content = "\n".join(lines) + "\n"
    result = write_and_commit_file(
        file_content=new_content,
        file_path="src/small.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Diff:" not in result.message
    assert "-line 5" in result.diff
    assert "+modified line 5" in result.diff


def test_no_diff_for_new_files(sample_base_args, tmp_path):
    """New files should not include a diff since there's nothing to diff against."""
    result = write_and_commit_file(
        file_content="\n".join(f"line {i}" for i in range(50)),
        file_path="src/brand_new.py",
        base_args=sample_base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert result.diff == ""


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


@pytest.mark.integration
def test_write_and_commit_file_end_to_end(local_repo, create_test_base_args):
    """Sociable: write new file, verify pushed to bare repo."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/write-test",
        )

        result = write_and_commit_file(
            file_content="print('new content')",
            file_path="new_file.py",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True
        assert os.path.isfile(os.path.join(clone_dir, "new_file.py"))

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--oneline", "feature/write-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "Create new_file.py" in log.stdout

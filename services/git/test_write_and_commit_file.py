# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from typing import cast
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git import write_and_commit_file as write_and_commit_file_mod
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import GitCommitResult
from services.git.write_and_commit_file import (
    WRITE_AND_COMMIT_FILE,
    write_and_commit_file,
)


def _ok_commit(**_kwargs):
    return GitCommitResult(success=True)


_PATCH_COMMIT = "services.git.write_and_commit_file.git_commit_and_push"


def test_replace_creates_new_file(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="print('hello')",
            file_path="src/test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Created src/test.py."
    assert result.file_path == "src/test.py"

    local_path = tmp_path / "src" / "test.py"
    assert local_path.exists()
    assert local_path.read_text() == "print('hello')\n"


def test_replace_existing_file(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("old content\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="new content",
            file_path="src/test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated src/test.py."
    assert (file_dir / "test.py").read_text() == "new content\n"


def test_skip_when_content_identical(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.py").write_text("same content\n")

    result = write_and_commit_file(
        file_content="same content\n",
        file_path="src/test.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=True,
        message="No changes to src/test.py.",
        file_path="src/test.py",
        content="same content\n",
    )


def test_directory_path_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    dir_path = tmp_path / "src"
    dir_path.mkdir()

    result = write_and_commit_file(
        file_content="content",
        file_path="src",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="'src' is a directory, not a file.",
        file_path="src",
        content="",
    )


def test_preserve_crlf_line_endings(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.ts").write_text("line1\r\nline2\r\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="line1\nline2_modified\n",
            file_path="src/test.ts",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated src/test.ts."
    with open(file_dir / "test.ts", "r", encoding="utf-8", newline="") as f:
        assert f.read() == "line1\r\nline2_modified\r\n"


def test_skip_when_content_identical_after_crlf_conversion(
    create_test_base_args, tmp_path
):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    (file_dir / "test.ts").write_text("line1\r\nline2\r\n")

    result = write_and_commit_file(
        file_content="line1\nline2\n",
        file_path="src/test.ts",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=True,
        message="No changes to src/test.ts.",
        file_path="src/test.ts",
        content="line1\r\nline2\r\n",
    )


def test_ensures_final_newline(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="no trailing newline",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "no trailing newline\n"


def test_extra_kwargs_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="content",
            file_path="test.py",
            base_args=base_args,
            extra_param="should_be_ignored",
            another_param=123,
        )

    assert result.success is True
    assert result.message == "Created test.py."


def test_nested_file_path(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="# deep file",
            file_path="src/utils/helpers/deep/nested/file.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "src/utils/helpers/deep/nested/file.py").exists()


def test_unicode_content(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="print('Hello 世界! 🌍 émojis')",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "print('Hello 世界! 🌍 émojis')\n"


def test_diff_included_for_existing_file(create_test_base_args, tmp_path):
    """When updating an existing file, the result message should include the unified diff."""
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    original = "\n".join(f"line {i}" for i in range(20)) + "\n"
    (file_dir / "big.py").write_text(original)

    new_content = "\n".join(f"replaced {i}" for i in range(15)) + "\n"
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content=new_content,
            file_path="src/big.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated src/big.py."
    diff_lines = result.diff.splitlines()
    # Every line 0..14 got rewritten; all 20 originals got removed
    removed = [ln for ln in diff_lines if ln.startswith("-line ")]
    added = [ln for ln in diff_lines if ln.startswith("+replaced ")]
    assert len(removed) >= 15
    assert len(added) >= 15


def test_diff_included_for_small_change(create_test_base_args, tmp_path):
    """Even small changes should include the diff."""
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    file_dir = tmp_path / "src"
    file_dir.mkdir()
    lines = [f"line {i}" for i in range(20)]
    original = "\n".join(lines) + "\n"
    (file_dir / "small.py").write_text(original)

    lines[5] = "modified line 5"
    new_content = "\n".join(lines) + "\n"
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content=new_content,
            file_path="src/small.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated src/small.py."
    diff_lines = result.diff.splitlines()
    assert diff_lines.count("-line 5") == 1
    assert diff_lines.count("+modified line 5") == 1


def test_no_diff_for_new_files(create_test_base_args, tmp_path):
    """New files should not include a diff since there's nothing to diff against."""
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = write_and_commit_file(
            file_content="\n".join(f"line {i}" for i in range(50)),
            file_path="src/brand_new.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.diff == ""


def test_tool_definition_structure():
    tool_def = cast(dict, WRITE_AND_COMMIT_FILE)
    assert tool_def["name"] == "write_and_commit_file"
    assert tool_def.get("description", "") != ""
    assert tool_def.get("strict") is True

    params = tool_def["input_schema"]
    if isinstance(params, dict):
        assert params.get("type") == "object"
        properties = params.get("properties", {})
        if isinstance(properties, dict):
            assert set(properties.keys()) == {"file_path", "file_content"}
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
            ["git", "log", "--format=%s", "feature/write-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert log.stdout.strip().splitlines()[0] == "Create new_file.py"


def test_write_and_commit_file_propagates_concurrent_push(
    create_test_base_args, tmp_path, monkeypatch
):
    """When git_commit_and_push reports a concurrent push, write_and_commit_file returns FileWriteResult with concurrent_push_detected=True so chat_with_agent can break the agent loop."""
    monkeypatch.setattr(
        write_and_commit_file_mod,
        "git_commit_and_push",
        lambda **kwargs: GitCommitResult(success=False, concurrent_push_detected=True),
    )

    base_args = create_test_base_args(
        skip_ci=False, clone_dir=str(tmp_path), new_branch="feature/raced"
    )
    result = write_and_commit_file(
        file_content="print('hi')",
        file_path="src/x.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="Concurrent push detected on `feature/raced` while committing src/x.py. Another commit landed on the branch; aborting this edit.",
        file_path="src/x.py",
        content="",
        concurrent_push_detected=True,
    )

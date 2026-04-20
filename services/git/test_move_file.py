# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileMoveResult
from services.git import move_file as move_file_mod
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import GitCommitResult
from services.git.move_file import move_file


def _ok_commit(**_kwargs):
    return GitCommitResult(success=True)


def test_same_file_paths_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    result = move_file("same/path.py", "same/path.py", base_args)
    assert result == FileMoveResult(
        success=False,
        message="Source and destination cannot be the same: 'same/path.py'.",
        old_file_path="same/path.py",
        new_file_path="same/path.py",
    )


def test_source_file_not_found(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    result = move_file("nonexistent/file.py", "new/path.py", base_args)
    assert result == FileMoveResult(
        success=False,
        message="File 'nonexistent/file.py' not found.",
        old_file_path="nonexistent/file.py",
        new_file_path="new/path.py",
    )


def test_target_file_already_exists(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "file.py").write_text("content")
    (tmp_path / "new").mkdir()
    (tmp_path / "new" / "file.py").write_text("existing")

    result = move_file("old/file.py", "new/file.py", base_args)
    assert result == FileMoveResult(
        success=False,
        message="Target file 'new/file.py' already exists.",
        old_file_path="old/file.py",
        new_file_path="new/file.py",
    )


def test_successful_move(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "file.py").write_text("test content")

    with patch("services.git.move_file.git_commit_and_push", side_effect=_ok_commit):
        result = move_file("old/file.py", "new/path.py", base_args)

    assert result == FileMoveResult(
        success=True,
        message="Moved old/file.py to new/path.py.",
        old_file_path="old/file.py",
        new_file_path="new/path.py",
    )
    assert not (old_dir / "file.py").exists()
    assert (tmp_path / "new" / "path.py").exists()
    assert (tmp_path / "new" / "path.py").read_text() == "test content"


def test_move_creates_parent_directories(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "src.py").write_text("content")

    with patch("services.git.move_file.git_commit_and_push", side_effect=_ok_commit):
        result = move_file("src.py", "deep/nested/dir/dest.py", base_args)

    assert isinstance(result, FileMoveResult)
    assert result.success is True
    assert (tmp_path / "deep" / "nested" / "dir" / "dest.py").exists()
    assert not (tmp_path / "src.py").exists()


def test_kwargs_parameter_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    result = move_file("same/path.py", "same/path.py", base_args, extra_param="ignored")
    assert result == FileMoveResult(
        success=False,
        message="Source and destination cannot be the same: 'same/path.py'.",
        old_file_path="same/path.py",
        new_file_path="same/path.py",
    )


def test_exception_handling_returns_result(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "my_dir").mkdir()

    result = move_file("my_dir", "new_dir", base_args)
    assert isinstance(result, FileMoveResult)


@pytest.mark.integration
def test_move_file_end_to_end(local_repo, create_test_base_args):
    """Sociable: move file in repo, verify pushed to bare repo."""
    bare_url, _work_dir = local_repo
    bare_dir = bare_url.replace("file://", "")

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/move-test",
        )

        assert os.path.isfile(os.path.join(clone_dir, "src", "main.py"))

        result = move_file("src/main.py", "src/renamed_main.py", base_args)

        assert isinstance(result, FileMoveResult)
        assert result.success is True
        assert not os.path.exists(os.path.join(clone_dir, "src", "main.py"))
        assert os.path.isfile(os.path.join(clone_dir, "src", "renamed_main.py"))

        log = subprocess.run(
            ["git", "log", "--format=%s", "feature/move-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert (
            log.stdout.strip().splitlines()[0]
            == "Move src/main.py to src/renamed_main.py"
        )


def test_move_file_propagates_concurrent_push(
    create_test_base_args, tmp_path, monkeypatch
):
    """Concurrent push from git_commit_and_push must bubble up as FileMoveResult(concurrent_push_detected=True) so chat_with_agent breaks the agent loop cleanly."""
    (tmp_path / "old.py").write_text("content")

    monkeypatch.setattr(
        move_file_mod,
        "git_commit_and_push",
        lambda **kwargs: GitCommitResult(success=False, concurrent_push_detected=True),
    )

    base_args = create_test_base_args(
        clone_dir=str(tmp_path), new_branch="feature/raced"
    )
    result = move_file(
        old_file_path="old.py",
        new_file_path="new.py",
        base_args=base_args,
    )

    assert result == FileMoveResult(
        success=False,
        message="Concurrent push detected on `feature/raced` while moving old.py to new.py. Another commit landed; aborting.",
        old_file_path="old.py",
        new_file_path="new.py",
        concurrent_push_detected=True,
    )

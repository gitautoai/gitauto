# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile

import pytest

from services.claude.tools.file_modify_result import FileMoveResult
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.move_file import move_file


@pytest.fixture
def base_args(create_test_base_args, tmp_path):
    return create_test_base_args(clone_dir=str(tmp_path))


def test_same_file_paths_error(base_args):
    result = move_file("same/path.py", "same/path.py", base_args)
    assert isinstance(result, FileMoveResult)
    assert result.success is False
    assert "same" in result.message


def test_source_file_not_found(base_args):
    result = move_file("nonexistent/file.py", "new/path.py", base_args)
    assert isinstance(result, FileMoveResult)
    assert result.success is False
    assert "not found" in result.message


def test_target_file_already_exists(base_args, tmp_path):
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "file.py").write_text("content")
    (tmp_path / "new").mkdir()
    (tmp_path / "new" / "file.py").write_text("existing")

    result = move_file("old/file.py", "new/file.py", base_args)
    assert isinstance(result, FileMoveResult)
    assert result.success is False
    assert "already exists" in result.message


def test_successful_move(base_args, tmp_path):
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "file.py").write_text("test content")

    result = move_file("old/file.py", "new/path.py", base_args)

    assert isinstance(result, FileMoveResult)
    assert result.success is True
    assert result.old_file_path == "old/file.py"
    assert result.new_file_path == "new/path.py"
    assert "Moved" in result.message
    assert not (old_dir / "file.py").exists()
    assert (tmp_path / "new" / "path.py").exists()
    assert (tmp_path / "new" / "path.py").read_text() == "test content"


def test_move_creates_parent_directories(base_args, tmp_path):
    (tmp_path / "src.py").write_text("content")

    result = move_file("src.py", "deep/nested/dir/dest.py", base_args)

    assert isinstance(result, FileMoveResult)
    assert result.success is True
    assert (tmp_path / "deep" / "nested" / "dir" / "dest.py").exists()
    assert not (tmp_path / "src.py").exists()


def test_kwargs_parameter_ignored(base_args):
    result = move_file("same/path.py", "same/path.py", base_args, extra_param="ignored")
    assert isinstance(result, FileMoveResult)
    assert result.success is False
    assert "same" in result.message


def test_exception_handling_returns_result(base_args, tmp_path):
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
            ["git", "log", "--oneline", "feature/move-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "Move src/main.py" in log.stdout

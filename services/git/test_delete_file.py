# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile

import pytest

from services.git.delete_file import delete_file
from services.git.git_clone_to_tmp import git_clone_to_tmp


def test_successful_deletion(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "test_file.py").write_text("content")

    result = delete_file("test_file.py", base_args)

    assert result == "File test_file.py successfully deleted"
    assert not (tmp_path / "test_file.py").exists()


def test_file_not_found(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    result = delete_file("nonexistent_file.py", base_args)
    assert result == "Error: File nonexistent_file.py not found"


def test_directory_path_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "my_dir").mkdir()

    result = delete_file("my_dir", base_args)
    assert result == "Error: 'my_dir' is a directory, not a file"


def test_nested_file_deletion(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    nested = tmp_path / "path" / "to" / "nested"
    nested.mkdir(parents=True)
    (nested / "file.py").write_text("content")

    result = delete_file("path/to/nested/file.py", base_args)

    assert result == "File path/to/nested/file.py successfully deleted"
    assert not (nested / "file.py").exists()


def test_kwargs_parameter_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(clone_dir=str(tmp_path))
    (tmp_path / "test_file.py").write_text("content")

    result = delete_file("test_file.py", base_args, extra_param="ignored")
    assert result == "File test_file.py successfully deleted"


@pytest.mark.integration
def test_delete_file_end_to_end(local_repo, create_test_base_args):
    """Sociable: delete file from repo, verify pushed to bare repo."""
    bare_url, _work_dir = local_repo
    bare_dir = bare_url.replace("file://", "")

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/delete-test",
        )

        assert os.path.isfile(os.path.join(clone_dir, "src", "main.py"))

        result = delete_file("src/main.py", base_args)

        assert result == "File src/main.py successfully deleted"
        assert not os.path.exists(os.path.join(clone_dir, "src", "main.py"))

        log = subprocess.run(
            ["git", "log", "--oneline", "feature/delete-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "Delete src/main.py" in log.stdout

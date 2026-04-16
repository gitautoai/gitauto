import os
import tempfile
from pathlib import Path

from utils.files.get_local_file_tree import get_local_file_tree


def test_lists_root_directory(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src"))
        os.makedirs(os.path.join(tmp, "node_modules"))
        Path(tmp, "README.md").touch()
        Path(tmp, "package.json").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args)

        assert "src/" in result
        assert "node_modules/" in result
        assert "README.md" in result
        assert "package.json" in result


def test_lists_subdirectory(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "node_modules", "@aws-sdk", "client-scheduler"))
        Path(
            tmp, "node_modules", "@aws-sdk", "client-scheduler", "package.json"
        ).touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(
            base_args=base_args,
            dir_path="node_modules/@aws-sdk/client-scheduler",
        )

        assert "package.json" in result


def test_nonexistent_directory_returns_empty(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args, dir_path="nonexistent")

        assert result == []


def test_empty_directory_returns_empty(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "empty"))

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args, dir_path="empty")

        assert result == []


def test_dirs_sorted_before_files(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "b_dir"))
        os.makedirs(os.path.join(tmp, "a_dir"))
        Path(tmp, "z_file.py").touch()
        Path(tmp, "a_file.py").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args)

        assert result == ["a_dir/", "b_dir/", "a_file.py", "z_file.py"]


def test_strips_slashes_from_dir_path(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src"))
        Path(tmp, "src", "main.py").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args, dir_path="/src/")

        assert "main.py" in result


def test_dot_dir_path_shows_root(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.txt").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args, dir_path=".")

        assert "file.txt" in result

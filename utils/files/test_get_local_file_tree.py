import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from utils.files.get_local_file_tree import get_local_file_tree


def test_lists_root_directory(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src"))
        os.makedirs(os.path.join(tmp, "node_modules"))
        Path(tmp, "README.md").touch()
        Path(tmp, "package.json").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args)

        assert result == ["node_modules/", "src/", "README.md", "package.json"]


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

        assert result == ["package.json"]


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

        assert result == ["main.py"]


def test_dot_dir_path_shows_root(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.txt").touch()

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_tree(base_args=base_args, dir_path=".")

        assert result == ["file.txt"]


def test_delegates_listing_to_list_local_directory(create_test_base_args):
    """The directory-listing logic moved into utils/files/list_local_directory.list_local_directory so it could be reused by read_local_file. get_local_file_tree should now just resolve clone_dir + dir_path and hand off — assert the helper is invoked with the resolved path and that we return whatever it returns verbatim."""
    base_args = create_test_base_args(clone_dir="/tmp/clone")
    expected = ["src/", "lib/", "README.md"]

    with patch(
        "utils.files.get_local_file_tree.list_local_directory",
        return_value=expected,
    ) as mock_listing:
        result = get_local_file_tree(base_args=base_args, dir_path="services/foo")

    assert result == expected
    mock_listing.assert_called_once_with("/tmp/clone/services/foo")

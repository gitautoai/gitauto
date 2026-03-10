import os
import tempfile
from unittest.mock import MagicMock

from services.git.create_directory import create_directory


def test_create_directory_creates_new_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_args = MagicMock()
        base_args.__getitem__ = lambda self, key: tmpdir if key == "clone_dir" else None

        result = create_directory(
            dir_path="tests/php/unit/Helpers", base_args=base_args
        )

        assert os.path.isdir(os.path.join(tmpdir, "tests/php/unit/Helpers"))
        assert "Created directory" in result


def test_create_directory_exist_ok():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_args = MagicMock()
        base_args.__getitem__ = lambda self, key: tmpdir if key == "clone_dir" else None

        os.makedirs(os.path.join(tmpdir, "existing/dir"))
        result = create_directory(dir_path="existing/dir", base_args=base_args)

        assert os.path.isdir(os.path.join(tmpdir, "existing/dir"))
        assert "Created directory" in result


def test_create_directory_strips_slashes():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_args = MagicMock()
        base_args.__getitem__ = lambda self, key: tmpdir if key == "clone_dir" else None

        result = create_directory(dir_path="/src/utils/", base_args=base_args)

        assert os.path.isdir(os.path.join(tmpdir, "src/utils"))
        assert "Created directory" in result

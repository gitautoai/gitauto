# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import pytest

from services.git.delete_file import delete_file


@pytest.fixture
def base_args(create_test_base_args, tmp_path):
    return create_test_base_args(clone_dir=str(tmp_path))


def test_successful_deletion(base_args, tmp_path):
    (tmp_path / "test_file.py").write_text("content")

    result = delete_file("test_file.py", base_args)

    assert result == "File test_file.py successfully deleted"
    assert not (tmp_path / "test_file.py").exists()


def test_file_not_found(base_args):
    result = delete_file("nonexistent_file.py", base_args)
    assert result == "Error: File nonexistent_file.py not found"


def test_directory_path_error(base_args, tmp_path):
    (tmp_path / "my_dir").mkdir()

    result = delete_file("my_dir", base_args)
    assert result == "Error: 'my_dir' is a directory, not a file"


def test_nested_file_deletion(base_args, tmp_path):
    nested = tmp_path / "path" / "to" / "nested"
    nested.mkdir(parents=True)
    (nested / "file.py").write_text("content")

    result = delete_file("path/to/nested/file.py", base_args)

    assert result == "File path/to/nested/file.py successfully deleted"
    assert not (nested / "file.py").exists()


def test_kwargs_parameter_ignored(base_args, tmp_path):
    (tmp_path / "test_file.py").write_text("content")

    result = delete_file("test_file.py", base_args, extra_param="ignored")
    assert result == "File test_file.py successfully deleted"

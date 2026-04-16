import os
import tempfile
from pathlib import Path

from utils.files.get_local_file_content import get_local_file_content


def test_reads_text_file_with_line_numbers(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "hello.py").write_text("print('hello')\nprint('world')\n")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="hello.py", base_args=base_args)

        assert "```hello.py" in result
        assert "1:print('hello')" in result
        assert "2:print('world')" in result


def test_file_not_found_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="nonexistent.py", base_args=base_args)

        assert "File not found" in result


def test_directory_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "subdir"))

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="subdir", base_args=base_args)

        assert "is a directory" in result


def test_empty_file(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "empty.py").write_text("")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="empty.py", base_args=base_args)

        assert "```empty.py" in result


def test_strips_leading_slash_from_file_path(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="/file.py", base_args=base_args)

        assert "content" in result


def test_multiple_params_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="file.py",
            base_args=base_args,
            line_number=1,
            keyword="content",
        )

        assert "Error: You can only specify one of" in result


def test_invalid_line_number_string_returns_error(create_test_base_args):
    """LLM can send strings for int params at runtime despite type hints."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        base_args = create_test_base_args(clone_dir=tmp)
        kwargs = {
            "file_path": "file.py",
            "base_args": base_args,
            "line_number": "abc",
        }
        result = get_local_file_content(**kwargs)

        assert "not a valid integer" in result


def test_start_line_greater_than_end_line_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="file.py",
            base_args=base_args,
            start_line=20,
            end_line=10,
        )

        assert "start_line must be less than or equal to end_line" in result


def test_truncation_ignored_for_small_files(create_test_base_args):
    """Files under 2000 lines should always return full content."""
    with tempfile.TemporaryDirectory() as tmp:
        lines = [f"line {i}" for i in range(100)]
        Path(tmp, "small.py").write_text("\n".join(lines))

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="small.py",
            base_args=base_args,
            start_line=10,
            end_line=20,
        )

        # Should contain all lines because file is under 2000 lines
        assert "line 0" in result
        assert "line 99" in result


def test_nested_file_path(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src", "utils"))
        Path(tmp, "src", "utils", "helper.py").write_text("def helper(): pass\n")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="src/utils/helper.py", base_args=base_args
        )

        assert "```src/utils/helper.py" in result
        assert "def helper(): pass" in result

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from utils.files.get_local_file_content import get_local_file_content


def test_reads_text_file_with_line_numbers(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "hello.py").write_text(
            "print('hello')\nprint('world')\n", encoding="utf-8"
        )

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="hello.py", base_args=base_args)

        assert result == "```hello.py\n1:print('hello')\n2:print('world')\n3:\n```"


def test_file_not_found_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="nonexistent.py", base_args=base_args)

        assert (
            result
            == "File not found: 'nonexistent.py'. Check the file path and try again."
        )


def test_directory_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "subdir"))

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="subdir", base_args=base_args)

        assert (
            result
            == "'subdir' is a directory, not a file. Use get_local_file_tree to list directory contents."
        )


def test_empty_file(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "empty.py").write_text("", encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="empty.py", base_args=base_args)

        assert result == "```empty.py\n1:\n```"


def test_strips_leading_slash_from_file_path(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n", encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(file_path="/file.py", base_args=base_args)

        assert result == "```/file.py\n1:content\n2:\n```"


def test_multiple_params_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n", encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="file.py",
            base_args=base_args,
            line_number=1,
            keyword="content",
        )

        assert (
            result
            == "Error: You can only specify one of: line_number, keyword, or start_line/end_line range."
        )


def test_invalid_line_number_string_returns_error(create_test_base_args):
    """LLM can send strings for int params at runtime despite type hints."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n", encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        kwargs = {
            "file_path": "file.py",
            "base_args": base_args,
            "line_number": "abc",
        }
        result = get_local_file_content(**kwargs)

        assert result == "Error: line_number 'abc' is not a valid integer."


def test_start_line_greater_than_end_line_returns_error(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n", encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="file.py",
            base_args=base_args,
            start_line=20,
            end_line=10,
        )

        assert result == "Error: start_line must be less than or equal to end_line."


def test_truncation_ignored_for_small_files(create_test_base_args):
    """Files under 1000 lines should always return full content."""
    with tempfile.TemporaryDirectory() as tmp:
        lines = [f"line {i}" for i in range(100)]
        Path(tmp, "small.py").write_text("\n".join(lines), encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="small.py",
            base_args=base_args,
            start_line=10,
            end_line=20,
        )

        # Files under 1000 lines ignore slicing and return full content.
        numbered = "\n".join(f"{i + 1:>3}:line {i}" for i in range(100))
        assert result == f"```small.py\n{numbered}\n```"


def test_keyword_ignored_for_small_files(create_test_base_args):
    """Keyword filter is ignored for small files — full content returned to prevent missing context."""
    with tempfile.TemporaryDirectory() as tmp:
        lines = [f"line {i}" for i in range(500)]
        lines[400] = "UNIQUE_KEYWORD_HERE"
        Path(tmp, "small.py").write_text("\n".join(lines), encoding="utf-8")

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="small.py",
            base_args=base_args,
            keyword="UNIQUE_KEYWORD_HERE",
        )

        numbered_lines = []
        for i, text in enumerate(lines):
            numbered_lines.append(f"{i + 1:>3}:{text}")
        numbered = "\n".join(numbered_lines)
        assert result == f"```small.py\n{numbered}\n```"


def test_nested_file_path(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src", "utils"))
        Path(tmp, "src", "utils", "helper.py").write_text(
            "def helper(): pass\n", encoding="utf-8"
        )

        base_args = create_test_base_args(clone_dir=tmp)
        result = get_local_file_content(
            file_path="src/utils/helper.py", base_args=base_args
        )

        assert result == "```src/utils/helper.py\n1:def helper(): pass\n2:\n```"


def test_image_file_threads_usage_id_and_created_by(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "img.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        base_args = create_test_base_args(
            clone_dir=tmp, usage_id=42, sender_id=7, sender_name="tester"
        )
        with patch(
            "utils.files.get_local_file_content.describe_image",
            return_value="a png",
        ) as mock_describe:
            get_local_file_content(file_path="img.png", base_args=base_args)

        kwargs = mock_describe.call_args.kwargs
        assert kwargs["usage_id"] == 42
        assert kwargs["created_by"] == "7:tester"

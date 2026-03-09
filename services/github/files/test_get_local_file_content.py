import os
import tempfile
from pathlib import Path
from typing import cast

from services.github.files.get_local_file_content import get_local_file_content
from services.github.types.github_types import BaseArgs


def _make_base_args(clone_dir: str):
    return cast(
        BaseArgs,
        {
            "owner_type": "Organization",
            "owner_id": 1,
            "owner": "test-owner",
            "repo_id": 1,
            "repo": "test-repo",
            "clone_url": "https://x-access-token:test-token@github.com/test-owner/test-repo.git",
            "is_fork": False,
            "pr_number": 1,
            "pr_title": "Test",
            "pr_body": "Test body",
            "pr_creator": "tester",
            "base_branch": "main",
            "new_branch": "feature",
            "installation_id": 1,
            "token": "test-token",
            "sender_id": 1,
            "sender_name": "tester",
            "sender_email": None,
            "reviewers": [],
            "github_urls": [],
            "other_urls": [],
            "clone_dir": clone_dir,
        },
    )


def test_reads_text_file_with_line_numbers():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "hello.py").write_text("print('hello')\nprint('world')\n")

        result = get_local_file_content(
            file_path="hello.py", base_args=_make_base_args(tmp)
        )

        assert "```hello.py" in result
        assert "1:print('hello')" in result
        assert "2:print('world')" in result


def test_file_not_found_returns_error():
    with tempfile.TemporaryDirectory() as tmp:
        result = get_local_file_content(
            file_path="nonexistent.py", base_args=_make_base_args(tmp)
        )

        assert "File not found" in result


def test_directory_returns_error():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "subdir"))

        result = get_local_file_content(
            file_path="subdir", base_args=_make_base_args(tmp)
        )

        assert "is a directory" in result


def test_empty_file():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "empty.py").write_text("")

        result = get_local_file_content(
            file_path="empty.py", base_args=_make_base_args(tmp)
        )

        assert "```empty.py" in result


def test_strips_leading_slash_from_file_path():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        result = get_local_file_content(
            file_path="/file.py", base_args=_make_base_args(tmp)
        )

        assert "content" in result


def test_multiple_params_returns_error():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        result = get_local_file_content(
            file_path="file.py",
            base_args=_make_base_args(tmp),
            line_number=1,
            keyword="content",
        )

        assert "Error: You can only specify one of" in result


def test_invalid_line_number_string_returns_error():
    """LLM can send strings for int params at runtime despite type hints."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        kwargs = {
            "file_path": "file.py",
            "base_args": _make_base_args(tmp),
            "line_number": "abc",
        }
        result = get_local_file_content(**kwargs)

        assert "not a valid integer" in result


def test_start_line_greater_than_end_line_returns_error():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.py").write_text("content\n")

        result = get_local_file_content(
            file_path="file.py",
            base_args=_make_base_args(tmp),
            start_line=20,
            end_line=10,
        )

        assert "start_line must be less than or equal to end_line" in result


def test_truncation_ignored_for_small_files():
    """Files under 2000 lines should always return full content."""
    with tempfile.TemporaryDirectory() as tmp:
        lines = [f"line {i}" for i in range(100)]
        Path(tmp, "small.py").write_text("\n".join(lines))

        result = get_local_file_content(
            file_path="small.py",
            base_args=_make_base_args(tmp),
            start_line=10,
            end_line=20,
        )

        # Should contain all lines because file is under 2000 lines
        assert "line 0" in result
        assert "line 99" in result


def test_nested_file_path():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src", "utils"))
        Path(tmp, "src", "utils", "helper.py").write_text("def helper(): pass\n")

        result = get_local_file_content(
            file_path="src/utils/helper.py", base_args=_make_base_args(tmp)
        )

        assert "```src/utils/helper.py" in result
        assert "def helper(): pass" in result

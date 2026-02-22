import os
import tempfile
from pathlib import Path
from typing import cast

from services.github.trees.get_local_file_tree import get_local_file_tree
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
            "clone_url": "https://github.com/test-owner/test-repo.git",
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
            "is_automation": False,
            "reviewers": [],
            "github_urls": [],
            "other_urls": [],
            "clone_dir": clone_dir,
        },
    )


def test_lists_root_directory():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src"))
        os.makedirs(os.path.join(tmp, "node_modules"))
        Path(tmp, "README.md").touch()
        Path(tmp, "package.json").touch()

        result = get_local_file_tree(base_args=_make_base_args(tmp))

        assert "src/" in result
        assert "node_modules/" in result
        assert "README.md" in result
        assert "package.json" in result


def test_lists_subdirectory():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "node_modules", "@aws-sdk", "client-scheduler"))
        Path(
            tmp, "node_modules", "@aws-sdk", "client-scheduler", "package.json"
        ).touch()

        result = get_local_file_tree(
            base_args=_make_base_args(tmp),
            dir_path="node_modules/@aws-sdk/client-scheduler",
        )

        assert "package.json" in result


def test_nonexistent_directory_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        result = get_local_file_tree(
            base_args=_make_base_args(tmp), dir_path="nonexistent"
        )

        assert result == []


def test_empty_directory_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "empty"))

        result = get_local_file_tree(base_args=_make_base_args(tmp), dir_path="empty")

        assert result == []


def test_dirs_sorted_before_files():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "b_dir"))
        os.makedirs(os.path.join(tmp, "a_dir"))
        Path(tmp, "z_file.py").touch()
        Path(tmp, "a_file.py").touch()

        result = get_local_file_tree(base_args=_make_base_args(tmp))

        assert result == ["a_dir/", "b_dir/", "a_file.py", "z_file.py"]


def test_strips_slashes_from_dir_path():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "src"))
        Path(tmp, "src", "main.py").touch()

        result = get_local_file_tree(base_args=_make_base_args(tmp), dir_path="/src/")

        assert "main.py" in result


def test_dot_dir_path_shows_root():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "file.txt").touch()

        result = get_local_file_tree(base_args=_make_base_args(tmp), dir_path=".")

        assert "file.txt" in result

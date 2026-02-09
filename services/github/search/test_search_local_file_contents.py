import os
import tempfile
from typing import cast
from unittest.mock import patch

import pytest

from config import UTF8
from services.github.search.search_local_file_contents import (
    search_local_file_contents,
)
from services.github.types.github_types import BaseArgs

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def _make_base_args(clone_dir: str) -> BaseArgs:
    # cast: partial mock object for testing
    return cast(BaseArgs, {"clone_dir": clone_dir})


def test_search_finds_matching_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w", encoding=UTF8) as f:
            f.write("def hello_world():\n    pass\n")
        with open(os.path.join(tmpdir, "src", "utils.py"), "w", encoding=UTF8) as f:
            f.write("import os\n")

        result = search_local_file_contents(
            query="hello_world", base_args=_make_base_args(tmpdir)
        )
        assert "1 files found" in result
        assert "src/main.py" in result


def test_search_no_matches():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w", encoding=UTF8) as f:
            f.write("def foo():\n    pass\n")

        result = search_local_file_contents(
            query="nonexistent_symbol", base_args=_make_base_args(tmpdir)
        )
        assert "0 files found" in result


def test_search_clone_dir_not_found():
    result = search_local_file_contents(
        query="test", base_args=_make_base_args("/nonexistent/path")
    )
    assert "Clone directory not found" in result


def test_search_excludes_node_modules():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "node_modules", "pkg"), exist_ok=True)
        with open(os.path.join(tmpdir, "node_modules", "pkg", "index.js"), "w", encoding=UTF8) as f:
            f.write("const myUniqueVar = 1;\n")
        with open(os.path.join(tmpdir, "app.js"), "w", encoding=UTF8) as f:
            f.write("const myUniqueVar = 2;\n")

        result = search_local_file_contents(
            query="myUniqueVar", base_args=_make_base_args(tmpdir)
        )
        assert "1 files found" in result
        assert "app.js" in result
        assert "node_modules" not in result


def test_search_multiple_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w", encoding=UTF8) as f:
            f.write("x = 1\n")
        with open(os.path.join(tmpdir, "b.py"), "w", encoding=UTF8) as f:
            f.write("x = 2\n")
        with open(os.path.join(tmpdir, "c.py"), "w", encoding=UTF8) as f:
            f.write("x = 3\n")

        result = search_local_file_contents(
            query="x = ", base_args=_make_base_args(tmpdir)
        )
        assert "3 files found" in result


def test_search_limits_to_20_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(25):
            with open(os.path.join(tmpdir, f"file_{i}.py"), "w", encoding=UTF8) as f:
                f.write("common_keyword = True\n")

        result = search_local_file_contents(
            query="common_keyword", base_args=_make_base_args(tmpdir)
        )
        assert "25 files found" in result
        assert "and 5 more files" in result


def test_search_grep_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "services.github.search.search_local_file_contents.subprocess.run"
        ) as mock_run:
            mock_run.return_value.returncode = 2
            mock_run.return_value.stderr = "grep: error"
            mock_run.return_value.stdout = ""

            result = search_local_file_contents(
                query="test", base_args=_make_base_args(tmpdir)
            )
            assert "Search failed" in result


@pytest.mark.integration
def test_search_real_repo():
    """Integration test: search this repo for a known unique function name."""
    result = search_local_file_contents(
        query="search_local_file_contents", base_args=_make_base_args(REPO_ROOT)
    )
    assert "files found" in result
    assert "search_local_file_contents.py" in result
    assert "node_modules" not in result
    assert "venv" not in result

import os
import tempfile
from unittest.mock import patch

import pytest

from config import UTF8
from utils.files.search_local_file_contents import (
    search_local_file_contents,
)

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def test_search_finds_matching_files(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w", encoding=UTF8) as f:
            f.write("def hello_world():\n    pass\n")
        with open(os.path.join(tmpdir, "src", "utils.py"), "w", encoding=UTF8) as f:
            f.write("import os\n")

        base_args = create_test_base_args(clone_dir=tmpdir)
        result = search_local_file_contents(query="hello_world", base_args=base_args)
        assert "1 files found" in result
        assert "src/main.py" in result
        assert "src/main.py:1:def hello_world():" in result


def test_search_no_matches(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w", encoding=UTF8) as f:
            f.write("def foo():\n    pass\n")

        base_args = create_test_base_args(clone_dir=tmpdir)
        result = search_local_file_contents(
            query="nonexistent_symbol", base_args=base_args
        )
        assert "0 files found" in result


def test_search_clone_dir_not_found(create_test_base_args):
    base_args = create_test_base_args(clone_dir="/nonexistent/path")
    result = search_local_file_contents(query="test", base_args=base_args)
    assert "0 files found" in result


def test_search_excludes_node_modules(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "node_modules", "pkg"), exist_ok=True)
        with open(
            os.path.join(tmpdir, "node_modules", "pkg", "index.js"), "w", encoding=UTF8
        ) as f:
            f.write("const myUniqueVar = 1;\n")
        with open(os.path.join(tmpdir, "app.js"), "w", encoding=UTF8) as f:
            f.write("const myUniqueVar = 2;\n")

        base_args = create_test_base_args(clone_dir=tmpdir)
        result = search_local_file_contents(query="myUniqueVar", base_args=base_args)
        assert "1 files found" in result
        assert "app.js" in result
        assert "node_modules" not in result


def test_search_multiple_files(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w", encoding=UTF8) as f:
            f.write("x = 1\n")
        with open(os.path.join(tmpdir, "b.py"), "w", encoding=UTF8) as f:
            f.write("x = 2\n")
        with open(os.path.join(tmpdir, "c.py"), "w", encoding=UTF8) as f:
            f.write("x = 3\n")

        base_args = create_test_base_args(clone_dir=tmpdir)
        result = search_local_file_contents(query="x = ", base_args=base_args)
        assert "3 files found" in result


def test_search_limits_to_20_files(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(25):
            with open(os.path.join(tmpdir, f"file_{i}.py"), "w", encoding=UTF8) as f:
                f.write("common_keyword = True\n")

        base_args = create_test_base_args(clone_dir=tmpdir)
        result = search_local_file_contents(query="common_keyword", base_args=base_args)
        assert "25 files found" in result
        assert "and 5 more files" in result


def test_search_grep_failure(create_test_base_args):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("utils.files.grep_files.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 2
            mock_run.return_value.stderr = "grep: error"
            mock_run.return_value.stdout = ""

            base_args = create_test_base_args(clone_dir=tmpdir)
            result = search_local_file_contents(query="test", base_args=base_args)
            assert "0 files found" in result


@pytest.mark.integration
def test_search_real_repo(create_test_base_args):
    """Integration test: search this repo for a known unique function name."""
    base_args = create_test_base_args(clone_dir=REPO_ROOT)
    result = search_local_file_contents(query="grep_files", base_args=base_args)
    assert "files found" in result
    assert "search_local_file_contents.py" in result
    # Verify excluded dirs don't appear as file paths (they may appear in line content)
    for line in result.split("\n"):
        if line.startswith("- "):
            file_path = line[2:].strip()
            assert not file_path.startswith(
                "node_modules/"
            ), f"Should exclude: {file_path}"
            assert not file_path.startswith("venv/"), f"Should exclude: {file_path}"

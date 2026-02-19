# pyright: reportUnusedVariable=false
import os
import subprocess

import pytest

from utils.files.apply_patch import apply_patch


@pytest.fixture
def clone_dir(tmp_path):
    """Create a git repo in a temp directory for git apply to work."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    return str(tmp_path)


def test_apply_simple_modification(clone_dir):
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2_modified\n"
        " line3\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "line2_modified" in result.content
    assert "line2\n" not in result.content


def test_apply_new_file(clone_dir):
    diff = (
        "--- /dev/null\n"
        "+++ b/new_file.txt\n"
        "@@ -0,0 +1,3 @@\n"
        "+line1\n"
        "+line2\n"
        "+line3\n"
    )
    result = apply_patch("", diff, clone_dir, "new_file.txt")
    assert result.error == ""
    assert "line1" in result.content
    assert "line2" in result.content
    assert "line3" in result.content


def test_apply_add_lines(clone_dir):
    original = "line1\nline2\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,2 +1,4 @@\n"
        " line1\n"
        "+added1\n"
        "+added2\n"
        " line2\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "added1" in result.content
    assert "added2" in result.content


def test_apply_remove_lines(clone_dir):
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,2 @@\n"
        " line1\n"
        "-line2\n"
        " line3\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "line2" not in result.content
    assert "line1" in result.content
    assert "line3" in result.content


def test_returns_error_on_bad_diff(clone_dir):
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " WRONG_CONTEXT\n"
        "-line2\n"
        "+line2_modified\n"
        " line3\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error != ""
    assert "stderr" in result.error


def test_preserves_crlf_line_endings(clone_dir):
    original = "line1\r\nline2\r\nline3\r\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2_modified\n"
        " line3\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "\r\n" in result.content


def test_empty_original_no_diff_returns_empty(clone_dir):
    result = apply_patch("", "", clone_dir, "file.txt")
    assert result.content == ""


def test_nested_file_path(clone_dir):
    """Test that nested file paths work (parent dirs created automatically)."""
    original = "content\n"
    diff = (
        "--- a/src/components/App.tsx\n"
        "+++ b/src/components/App.tsx\n"
        "@@ -1 +1 @@\n"
        "-content\n"
        "+new_content\n"
    )
    result = apply_patch(original, diff, clone_dir, "src/components/App.tsx")
    assert result.error == ""
    assert "new_content" in result.content
    assert os.path.exists(os.path.join(clone_dir, "src/components/App.tsx"))

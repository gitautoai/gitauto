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


def test_apply_new_file_without_ab_prefix(clone_dir):
    """Test new file creation when diff uses raw paths instead of a/ b/ prefix.
    This is the exact format Claude generates: '--- /dev/null' and '+++ file_path'
    without the 'b/' prefix. git apply fails on this format."""
    diff = (
        "--- /dev/null\n"
        "+++ src/resolvers/getUserResolver.test.ts\n"
        "@@ -0,0 +1,3 @@\n"
        "+import getUserResolver from './getUserResolver';\n"
        "+\n"
        "+describe('getUserResolver', () => {});\n"
    )
    result = apply_patch("", diff, clone_dir, "src/resolvers/getUserResolver.test.ts")
    assert result.error == ""
    assert "getUserResolver" in result.content


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


def test_error_message_wraps_diff_in_code_fences(clone_dir):
    # Diff output contains --- and +++ which render as Markdown headings if not fenced
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
    assert "```" in result.error


def test_zero_context_import_reorder_mid_file(clone_dir):
    # Reproduces exact failure from sample-calculator PR #10: Claude wrote a test file
    # then tried to reorder imports via apply_diff_to_file. The diff had only 1 trailing
    # context line and removed/added empty lines between import groups. Without
    # --unidiff-zero, git apply fails because it requires ~3 context lines to locate hunks.
    original = (
        "import math\n"
        "from unittest.mock import patch\n"
        "\n"
        "from calculator import add, divide, main, multiply, subtract\n"
        "\n"
        "import pytest\n"
        "\n"
        "\n"
        "class TestAdd:\n"
        "    def test_positive_integers(self):\n"
        "        assert True\n"
    )
    diff = (
        "--- a/test_calculator.py\n"
        "+++ b/test_calculator.py\n"
        "@@ -4,3 +4,3 @@\n"
        "-from calculator import add, divide, main, multiply, subtract\n"
        "-\n"
        " import pytest\n"
        "+\n"
        "+from calculator import add, divide, main, multiply, subtract\n"
    )
    result = apply_patch(original, diff, clone_dir, "test_calculator.py")
    assert result.error == ""
    # pytest should now come before calculator imports
    pytest_pos = result.content.index("import pytest")
    calc_pos = result.content.index("from calculator import")
    assert pytest_pos < calc_pos


def test_zero_context_empty_line_removal_mid_file(clone_dir):
    # Hunk removes an empty line (just "-\n" in diff) in the middle of a file.
    # Without --unidiff-zero, git apply can't locate the hunk among nearby empty lines.
    original = "line1\nline2\nline3\naaa\n\nbbb\n\nline8\nline9\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -4,3 +4,3 @@\n"
        "-aaa\n"
        "-\n"
        " bbb\n"
        "+\n"
        "+aaa\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "bbb\n\naaa\n" in result.content


def test_zero_context_pure_addition_mid_file(clone_dir):
    # Pure addition hunk (no context lines at all) inserted in the middle of a file.
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -2,0 +3,2 @@\n"
        "+added1\n"
        "+added2\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "line2\nadded1\nadded2\nline3\n" in result.content


def test_zero_context_pure_deletion_mid_file(clone_dir):
    # Pure deletion hunk (no context lines) removing lines from the middle of a file.
    original = "line1\nline2\nline3\nline4\nline5\n"
    diff = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -3,2 +3,0 @@\n"
        "-line3\n"
        "-line4\n"
    )
    result = apply_patch(original, diff, clone_dir, "file.txt")
    assert result.error == ""
    assert "line3" not in result.content
    assert "line4" not in result.content
    assert "line2\nline5\n" in result.content

import subprocess
import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from utils.files.apply_patch import apply_patch


def test_apply_patch_simple_modification():
    """Test applying a simple patch to modify existing content."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run") as mock_run:
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert "line 2 modified" in result


def test_apply_patch_new_file_creation():
    """Test creating a new file with a patch."""
    original_text = ""
    diff_text = """--- /dev/null
+++ new_file.txt
@@ -0,0 +1,3 @@
+line 1
+line 2
+line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert result == "line 1\nline 2\nline 3\n"


def test_apply_patch_file_deletion():
    """Test handling file deletion case."""
    original_text = "line 1\nline 2\n"
    diff_text = """--- test.txt
+++ /dev/null
@@ -1,2 +0,0 @@
-line 1
-line 2
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("os.path.exists", return_value=False):
                with patch("os.remove"):
                    with patch("os.listdir", return_value=[]):
                        result, error = apply_patch(original_text, diff_text)

    assert result == ""
    assert error == ""


def test_apply_patch_with_crlf_line_endings():
    """Test applying patch with CRLF line endings."""
    original_text = "line 1\r\nline 2\r\nline 3\r\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\r\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert "\r\n" in result


def test_apply_patch_with_cr_line_endings():
    """Test applying patch with CR line endings."""
    original_text = "line 1\rline 2\rline 3\r"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\r"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert "\r" in result


def test_apply_patch_original_text_without_final_newline():
    """Test applying patch when original text doesn't end with newline."""
    original_text = "line 1\nline 2\nline 3"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""


def test_apply_patch_diff_without_final_newline():
    """Test applying patch when diff text doesn't end with newline."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""


def test_apply_patch_already_applied_with_already_exists():
    """Test handling patch that was already applied (already exists message)."""
    original_text = "line 1\nline 2 modified\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        mock_error = subprocess.CalledProcessError(1, "patch")
        mock_error.stdout = "File already exists!"
        mock_error.stderr = "Error applying patch"
        with patch("subprocess.run", side_effect=mock_error):
            with patch("os.remove"):
                with patch("os.listdir", return_value=[]):
                    result, error = apply_patch(original_text, diff_text)

    assert result == ""
    assert "already applied" in error
    assert "diff_text:" in error


def test_apply_patch_already_applied_with_ignoring_message():
    """Test handling patch that was already applied (ignoring message)."""
    original_text = "line 1\nline 2 modified\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        mock_error = subprocess.CalledProcessError(1, "patch")
        mock_error.stdout = "Ignoring previously applied (or reversed) patch."
        mock_error.stderr = "Error applying patch"
        with patch("subprocess.run", side_effect=mock_error):
            with patch("os.remove"):
                with patch("os.listdir", return_value=[]):
                    result, error = apply_patch(original_text, diff_text)

    assert result == ""
    assert "already applied" in error


def test_apply_patch_failed_with_reject_file():
    """Test handling patch failure with reject file."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        mock_error = subprocess.CalledProcessError(1, "patch")
        mock_error.stdout = "Hunk #1 FAILED"
        mock_error.stderr = "Error applying patch"
        with patch("subprocess.run", side_effect=mock_error):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.side_effect = [
                                            "line 1\nline 2\nline 3\n",
                                            "--- test.txt\n+++ test.txt\n",
                                            "rejected hunk"
                                        ]
                                        result, error = apply_patch(original_text, diff_text)

    assert "Failed to apply patch partially or entirelly" in error
    assert "stderr:" in error
    assert "rej_text:" in error


def test_apply_patch_failed_without_reject_file():
    """Test handling patch failure without reject file."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        mock_error = subprocess.CalledProcessError(1, "patch")
        mock_error.stdout = "Hunk #1 FAILED"
        mock_error.stderr = "Error applying patch"
        with patch("subprocess.run", side_effect=mock_error):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", side_effect=lambda x: not x.endswith(".rej")):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.side_effect = [
                                            "line 1\nline 2\nline 3\n",
                                            "--- test.txt\n+++ test.txt\n"
                                        ]
                                        result, error = apply_patch(original_text, diff_text)

    assert "Failed to apply patch partially or entirelly" in error
    assert "rej_text:" in error


def test_apply_patch_file_not_found_error():
    """Test handling FileNotFoundError."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run", side_effect=FileNotFoundError("patch command not found")):
            with patch("os.remove"):
                with patch("os.listdir", return_value=[]):
                    result, error = apply_patch(original_text, diff_text)

    assert result == ""
    assert "Error:" in error
    assert "patch command not found" in error


def test_apply_patch_generic_exception():
    """Test handling generic exception."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run", side_effect=Exception("Unexpected error")):
            with patch("os.remove"):
                with patch("os.listdir", return_value=[]):
                    result, error = apply_patch(original_text, diff_text)

    assert result == ""
    assert "Error:" in error
    assert "Unexpected error" in error


def test_apply_patch_cleanup_temp_files():
    """Test that temporary files are cleaned up."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove") as mock_remove:
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert mock_remove.call_count >= 2


def test_apply_patch_cleanup_fails_for_org_file():
    """Test handling cleanup failure for original file."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove", side_effect=[Exception("Cannot remove"), None]):
                                    with patch("os.listdir", return_value=[]):
                                        with patch("builtins.print") as mock_print:
                                            mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                            result, error = apply_patch(original_text, diff_text)

    assert error == ""
    mock_print.assert_any_call("Failed to remove org file: Cannot remove")


def test_apply_patch_cleanup_fails_for_diff_file():
    """Test handling cleanup failure for diff file."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove", side_effect=[None, Exception("Cannot remove diff")]):
                                    with patch("os.listdir", return_value=[]):
                                        with patch("builtins.print") as mock_print:
                                            mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                            result, error = apply_patch(original_text, diff_text)

    assert error == ""
    mock_print.assert_any_call("Failed to remove diff file: Cannot remove diff")


def test_apply_patch_cleanup_oops_rej_files():
    """Test cleanup of Oops.rej files."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("subprocess.run"):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove") as mock_remove:
                                    with patch("os.listdir", return_value=["Oops.rej", "Oops.rej.orig", "other.txt"]):
                                        with patch("os.getcwd", return_value="/test/dir"):
                                            mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                                            result, error = apply_patch(original_text, diff_text)

    remove_calls = [str(call) for call in mock_remove.call_args_list]
    assert any("Oops.rej" in call for call in remove_calls)


def test_apply_patch_empty_original_text():
    """Test applying patch with empty original text."""
    original_text = ""
    diff_text = """--- /dev/null
+++ new_file.txt
@@ -0,0 +1,2 @@
+new line 1
+new line 2
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        with patch("builtins.open", mock_open()):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=True):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.return_value = "new line 1\nnew line 2\n"
                                        result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert "new line 1" in result


def test_apply_patch_with_special_characters():
    """Test applying patch with special characters in diff."""
    original_text = "line 1\nline 2\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,2 +1,2 @@
 line 1
-line 2
+line 2 with tabs\tand spaces
"""

    with patch("utils.files.apply_patch.detect_line_break", return_value="\n"):
        mock_error = subprocess.CalledProcessError(1, "patch")
        mock_error.stdout = "Failed"
        mock_error.stderr = "Error"
        with patch("subprocess.run", side_effect=mock_error):
            with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
                with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                    with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                        with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                            with patch("os.path.exists", return_value=False):
                                with patch("os.remove"):
                                    with patch("os.listdir", return_value=[]):
                                        mock_get_content.side_effect = [
                                            "line 1\nline 2\n",
                                            "diff with\ttabs and spaces"
                                        ]
                                        result, error = apply_patch(original_text, diff_text)

    assert "→" in error
    assert "·" in error


def test_apply_patch_integration_with_real_temp_files():
    """Test apply_patch with real temporary files (integration test)."""
    original_text = "line 1\nline 2\nline 3\n"
    diff_text = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

    with patch("subprocess.run"):
        with patch("utils.files.apply_patch.get_file_content") as mock_get_content:
            with patch("utils.files.apply_patch.sort_imports", side_effect=lambda x, y: x):
                with patch("utils.files.apply_patch.strip_trailing_spaces", side_effect=lambda x: x):
                    with patch("utils.files.apply_patch.ensure_final_newline", side_effect=lambda x: x):
                        with patch("os.path.exists", return_value=True):
                            mock_get_content.return_value = "line 1\nline 2 modified\nline 3\n"
                            result, error = apply_patch(original_text, diff_text)

    assert error == ""
    assert "line 2 modified" in result

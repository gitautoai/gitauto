from unittest.mock import patch

import pytest
from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_remove_pytest_sections_with_empty_input():
    """Test that empty string input returns empty string."""
    assert remove_pytest_sections("") == ""


def test_remove_pytest_sections_with_none_input():
    """Test that None input returns None."""
    assert remove_pytest_sections(None) is None


def test_remove_pytest_sections_with_no_pytest_markers():
    """Test that logs without pytest markers remain unchanged."""
    log = "Some regular error log\nwithout pytest markers\nshould remain unchanged"
    assert remove_pytest_sections(log) == log


def test_remove_pytest_sections_with_test_session_starts():
    """Test removal of test session starts section."""
    log = """Run python -m pytest
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /github/workspace
plugins: cov-6.0.0
collecting ... collected 2 items

test_example.py::test_pass PASSED                                       [ 50%]
test_example.py::test_fail FAILED                                       [100%]

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError
=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

    expected = """Run python -m pytest

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_warnings_summary():
    """Test removal of warnings summary section."""
    log = """Some initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  warnings.warn("deprecated", DeprecationWarning)

-- Docs: https://docs.python.org/3/library/warnings.html

=================================== FAILURES ===================================
Test failure content"""

    expected = """Some initial content

=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_both_session_and_warnings():
    """Test removal of both test session starts and warnings summary sections."""
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
=========================== warnings summary ============================
warning content
=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_blank_line_insertion():
    """Test that blank line is added before FAILURES when content was removed."""
    log = """Initial content
=========================== test session starts ============================
removed content
=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_no_blank_line_when_last_line_blank():
    """Test that no extra blank line is added before FAILURES when last line is already blank."""
    log = """Initial content

=========================== test session starts ============================
removed content
=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_no_blank_line_when_no_content_removed():
    """Test that no blank line is added before FAILURES when no content was removed."""
    log = """Initial content
=================================== FAILURES ===================================
failure content"""

    expected = """Initial content
=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_blank_line_insertion():
    """Test that blank line is added before short test summary when content was removed."""
    log = """Initial content
=========================== test session starts ============================
removed content
=========================== short test summary info ============================
summary content"""

    expected = """Initial content

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_no_blank_line_when_last_line_blank():
    """Test that no extra blank line is added before short summary when last line is already blank."""
    log = """Initial content

=========================== test session starts ============================
removed content
=========================== short test summary info ============================
summary content"""

    expected = """Initial content

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_no_blank_line_when_no_content_removed():
    """Test that no blank line is added before short summary when no content was removed."""
    log = """Initial content
=========================== short test summary info ============================
summary content"""

    expected = """Initial content
=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_removes_excessive_blank_lines_when_content_removed():
    """Test that excessive blank lines are cleaned up when content is removed."""
    log = """Line 1


=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
test content that will be removed




=========================== short test summary info ============================
Line 2




Line 3"""
    expected = """Line 1

=========================== short test summary info ============================
Line 2

Line 3"""
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_preserves_blank_lines_when_no_content_removed():
    """Test that blank lines are preserved when no content is removed."""
    log = """Line 1




Line 2




Line 3"""
    expected = """Line 1




Line 2




Line 3"""
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_complex_scenario():
    """Test a complex scenario with multiple sections and edge cases."""
    log = """Build started
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /github/workspace
plugins: cov-6.0.0
collecting ... collected 5 items

test_file1.py::test_one PASSED                                          [ 20%]
test_file1.py::test_two FAILED                                          [ 40%]
test_file2.py::test_three PASSED                                        [ 60%]
test_file2.py::test_four FAILED                                         [ 80%]
test_file2.py::test_five PASSED                                         [100%]

=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  warnings.warn("deprecated", DeprecationWarning)

-- Docs: https://docs.python.org/3/library/warnings.html

=================================== FAILURES ===================================
_______________________________ test_two __________________________________

    def test_two():
>       assert False
E       AssertionError

test_file1.py:5: AssertionError

_______________________________ test_four __________________________________

    def test_four():
>       assert 1 == 2
E       AssertionError

test_file2.py:10: AssertionError

=========================== short test summary info ============================
FAILED test_file1.py::test_two - AssertionError
FAILED test_file2.py::test_four - AssertionError
========================= 2 failed, 3 passed in 0.50s ========================="""

    expected = """Build started

=================================== FAILURES ===================================
_______________________________ test_two __________________________________

    def test_two():
>       assert False
E       AssertionError

test_file1.py:5: AssertionError

_______________________________ test_four __________________________________

    def test_four():
>       assert 1 == 2
E       AssertionError

test_file2.py:10: AssertionError

=========================== short test summary info ============================
FAILED test_file1.py::test_two - AssertionError
FAILED test_file2.py::test_four - AssertionError
========================= 2 failed, 3 passed in 0.50s ========================="""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_test_session_starts():
    """Test removal when only test session starts section is present."""
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_warnings_summary():
    """Test removal when only warnings summary section is present."""
    log = """Initial content
=========================== warnings summary ============================
warning content
Final content"""

    expected = """Initial content
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_partial_matches_not_removed():
    """Test that partial matches in section headers are not removed."""
    log = """Initial content
Some line with === but no test session starts
Another line with warnings summary but no ===
Line with === and FAILURES but not exact match
Line with === and short test summary but not exact match
Final content"""

    expected = """Initial content
Some line with === but no test session starts
Another line with warnings summary but no ===
Line with === and FAILURES but not exact match
Line with === and short test summary but not exact match
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_empty_filtered_lines():
    """Test handling when filtered_lines is empty before adding blank line."""
    log = """=========================== test session starts ============================
removed content
=================================== FAILURES ===================================
failure content"""

    expected = """=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


@patch('utils.logs.remove_pytest_sections.handle_exceptions')
def test_remove_pytest_sections_exception_handling(mock_handle_exceptions):
    """Test that the function is decorated with handle_exceptions."""
    # The decorator should be applied to the function
    mock_handle_exceptions.assert_called_once_with(default_return_value="")


def test_remove_pytest_sections_with_exception_returns_empty_string():
    """Test that exceptions are handled and return empty string as default."""
    # This test verifies the decorator behavior by causing an exception
    # We'll patch the split method to raise an exception
    with patch.object(str, 'split', side_effect=Exception("Test exception")):
        result = remove_pytest_sections("test input")
        # The handle_exceptions decorator should catch the exception and return ""
        assert result == ""


def test_remove_pytest_sections_single_line_input():
    """Test handling of single line input without newlines."""
    log = "Single line without pytest markers"
    expected = "Single line without pytest markers"
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_single_line_with_marker():
    """Test handling of single line input with pytest marker."""
    log = "=========================== test session starts ============================"
    expected = ""
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_only():
    """Test when input contains only FAILURES section."""
    log = """=================================== FAILURES ===================================
failure content"""
    expected = """=================================== FAILURES ===================================
failure content"""
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_only():
    """Test when input contains only short test summary section."""
    log = """=========================== short test summary info ============================
summary content"""
    expected = """=========================== short test summary info ============================
summary content"""
    result = remove_pytest_sections(log)
    assert result == expected

from unittest.mock import patch

import pytest
from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_remove_pytest_sections_with_pytest_output():
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


def test_remove_pytest_sections_with_empty_input():
    assert remove_pytest_sections("") == ""


def test_remove_pytest_sections_with_none_input():
    assert remove_pytest_sections(None) is None


def test_remove_pytest_sections_with_no_pytest_markers():
    log = "Some regular error log\nwithout pytest markers\nshould remain unchanged"
    assert remove_pytest_sections(log) == log


def test_remove_pytest_sections_removes_excessive_blank_lines_when_content_removed():
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


def test_remove_pytest_sections_with_warnings_summary():
    log = """Some initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

-- Docs: https://docs.pytest.org/en/stable/how.html#warnings
=================================== FAILURES ===================================
Test failure content"""

    expected = """Some initial content

=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_failures_no_previous_content():
    log = """=================================== FAILURES ===================================
Test failure content"""

    expected = """=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_failures_last_line_already_blank():
    log = """Some content

=========================== test session starts ============================
removed content
=================================== FAILURES ===================================
Test failure content"""

    expected = """Some content

=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_summary_no_previous_content():
    log = """=========================== short test summary info ============================
Summary content"""

    expected = """=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_summary_last_line_already_blank():
    log = """Some content

=========================== test session starts ============================
removed content
=========================== short test summary info ============================
Summary content"""

    expected = """Some content

=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_multiple_sections():
    log = """Initial content
=========================== test session starts ============================
platform info
collected items
=========================== warnings summary ============================
warning content
=================================== FAILURES ===================================
failure content
=========================== short test summary info ============================
summary content
Final content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content

=========================== short test summary info ============================
summary content
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_partial_matches_not_removed():
    log = """This line has equals but no test session starts
This line has test session starts but no equals
This line has equals and warnings but not warnings summary
This line has equals and FAILED but not FAILURES
This line has equals and short test but not summary info"""

    # Should remain unchanged since none match the exact patterns
    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_case_sensitive():
    log = """=========================== test session starts ============================
should be removed
=================================== failures ===================================
should NOT be removed (lowercase)
=========================== short test summary info ============================
should be removed"""

    expected = """=========================== short test summary info ============================
should be removed"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_removes_excessive_blank_lines_when_content_removed():
    log = """Line 1




Line 2"""

    # Should remain unchanged since no content was removed
    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_handles_single_line_input():
    log = "=========================== test session starts ============================"
    expected = ""
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_exception_handling():
    """Test that the decorator handles exceptions properly"""
    with patch('utils.logs.remove_pytest_sections.re.sub', side_effect=Exception("Test exception")):
        # Use input that will trigger content removal and thus call re.sub
        # This will cause re.sub to raise an exception, which should be caught by the decorator
        test_input = "=========================== test session starts ============================\nremoved content"
        result = remove_pytest_sections(test_input)
        assert result == ""


def test_remove_pytest_sections_preserves_content_between_sections():
    log = """Before session
=========================== test session starts ============================
removed session content
Some important content between sections
=========================== warnings summary ============================
removed warnings content
More important content
=================================== FAILURES ===================================
failure content
Content after failures
=========================== short test summary info ============================
summary content
After summary"""

    expected = """Before session
Some important content between sections
More important content

=================================== FAILURES ===================================
failure content
Content after failures

=========================== short test summary info ============================
summary content
After summary"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_empty_lines_only():
    log = """


"""
    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_mixed_line_endings():
    """Test with different line ending scenarios"""
    log = "Line 1\n=========================== test session starts ============================\nremoved\n=================================== FAILURES ===================================\nfailure"
    expected = "Line 1\n\n=================================== FAILURES ===================================\nfailure"
    result = remove_pytest_sections(log)
    assert result == expected

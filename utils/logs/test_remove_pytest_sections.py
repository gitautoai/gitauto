from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_remove_pytest_sections_with_pytest_output():
    """Test removing pytest session header and keeping failures section."""
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
    """Test that empty string returns empty string."""
    assert remove_pytest_sections("") == ""


def test_remove_pytest_sections_with_none_input():
    """Test that None input returns None."""
    assert remove_pytest_sections(None) is None


def test_remove_pytest_sections_with_no_pytest_markers():
    """Test that logs without pytest markers remain unchanged."""
    log = "Some regular error log\nwithout pytest markers\nshould remain unchanged"
    assert remove_pytest_sections(log) == log


def test_remove_pytest_sections_removes_excessive_blank_lines_when_content_removed():
    """Test that excessive blank lines are reduced to double blank lines when content is removed."""
    log = """Line 1


=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0




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
    """Test removing warnings summary section."""
    log = """Some initial content
=========================== warnings summary ============================
test_example.py::test_something
  /path/to/file.py:10: DeprecationWarning: something is deprecated
    warnings.warn("something is deprecated")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== FAILURES ===================================
Test failure details"""

    expected = """Some initial content

=================================== FAILURES ===================================
Test failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_both_session_and_warnings():
    """Test removing both test session and warnings summary sections."""
    log = """Initial log
=========================== test session starts ============================
platform linux -- Python 3.11.4
collected 5 items
=========================== warnings summary ============================
test_file.py
  Warning details here
=================================== FAILURES ===================================
Failure details"""

    expected = """Initial log

=================================== FAILURES ===================================
Failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_blank_line_before():
    """Test that blank line is added before FAILURES when last line is not blank (covers line 32 branch)."""
    log = """Some content line
=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
Failure content"""

    expected = """Some content line

=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_without_blank_line_when_last_is_blank():
    """Test that no extra blank line is added before FAILURES when last line is already blank."""
    log = """Some content line

=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
Failure content"""

    expected = """Some content line

=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_summary_with_blank_line_before():
    """Test that blank line is added before short test summary when last line is not blank."""
    log = """Some content line
=========================== test session starts ============================
session content to remove
=========================== short test summary info ============================
Summary content"""

    expected = """Some content line

=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_summary_without_blank_line_when_last_is_blank():
    """Test that no extra blank line is added before summary when last line is already blank."""
    log = """Some content line

=========================== test session starts ============================
session content to remove
=========================== short test summary info ============================
Summary content"""

    expected = """Some content line

=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_session_header():
    """Test removing only test session header without failures or summary."""
    log = """Before session
=========================== test session starts ============================
platform linux -- Python 3.11.4
collected 10 items
test_file.py .......... [100%]
After session"""

    expected = """Before session
After session"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_warnings():
    """Test removing only warnings summary without other sections."""
    log = """Before warnings
=========================== warnings summary ============================
test_file.py
  Warning details
After warnings"""

    expected = """Before warnings
After warnings"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_at_start():
    """Test FAILURES section at the start without content_removed flag set."""
    log = """=================================== FAILURES ===================================
Failure details
More failure info"""

    expected = """=================================== FAILURES ===================================
Failure details
More failure info"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_summary_at_start():
    """Test short test summary at the start without content_removed flag set."""
    log = """=========================== short test summary info ============================
FAILED test_example.py::test_fail
Summary details"""

    expected = """=========================== short test summary info ============================
FAILED test_example.py::test_fail
Summary details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_no_excessive_blanks_without_content_removal():
    """Test that excessive blank lines are NOT reduced when no content is removed."""
    log = """Line 1



Line 2



Line 3"""

    expected = """Line 1



Line 2



Line 3"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_complex_scenario():
    """Test complex scenario with multiple sections and edge cases."""
    log = """Initial output
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0
rootdir: /workspace
collected 10 items

test_file1.py::test_one PASSED
test_file2.py::test_two FAILED

=========================== warnings summary ============================
test_file1.py::test_one
  DeprecationWarning: old function
test_file2.py::test_two
  UserWarning: something

=================================== FAILURES ===================================
_______________________________ test_two _________________________________

    def test_two():
>       assert 1 == 2
E       AssertionError

test_file2.py:5: AssertionError

=========================== short test summary info ============================
FAILED test_file2.py::test_two - AssertionError
========================= 1 failed, 1 passed in 0.50s ========================="""

    expected = """Initial output

=================================== FAILURES ===================================
_______________________________ test_two _________________________________

    def test_two():
>       assert 1 == 2
E       AssertionError

test_file2.py:5: AssertionError

=========================== short test summary info ============================
FAILED test_file2.py::test_two - AssertionError
========================= 1 failed, 1 passed in 0.50s ========================="""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_partial_markers():
    """Test that partial matches don't trigger section removal."""
    log = """This line has === but not test session starts
This line mentions test session starts but no ===
=== This has equals but wrong text
Normal content should remain"""

    expected = """This line has === but not test session starts
This line mentions test session starts but no ===
=== This has equals but wrong text
Normal content should remain"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_empty_filtered_lines_before_failures():
    """Test FAILURES section when filtered_lines is empty (edge case for line 32)."""
    log = """=========================== test session starts ============================
session content
=================================== FAILURES ===================================
Failure content"""

    expected = """=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_empty_filtered_lines_before_summary():
    """Test short test summary when filtered_lines is empty."""
    log = """=========================== test session starts ============================
session content
=========================== short test summary info ============================
Summary content"""

    expected = """=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_single_line_input():
    """Test with single line input."""
    log = "Single line without any markers"
    expected = "Single line without any markers"
    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_markers():
    """Test with only pytest markers and no other content."""
    log = """=========================== test session starts ============================
=========================== warnings summary ============================
=================================== FAILURES ===================================
=========================== short test summary info ============================"""

    expected = """=================================== FAILURES ===================================

=========================== short test summary info ============================"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_multiple_failures_sections():
    """Test with multiple FAILURES sections."""
    log = """Content before
=========================== test session starts ============================
session data
=================================== FAILURES ===================================
First failure
=================================== FAILURES ===================================
Second failure"""

    expected = """Content before

=================================== FAILURES ===================================
First failure
=================================== FAILURES ===================================
Second failure"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_case_sensitive():
    """Test that section detection is case-sensitive."""
    log = """Content
=========================== TEST SESSION STARTS ============================
Should not be removed (uppercase)
=========================== Test Session Starts ============================
Should not be removed (title case)
=========================== failures ============================
Should not be removed (lowercase)"""

    expected = """Content
=========================== TEST SESSION STARTS ============================
Should not be removed (uppercase)
=========================== Test Session Starts ============================
Should not be removed (title case)
=========================== failures ============================
Should not be removed (lowercase)"""

    result = remove_pytest_sections(log)
    assert result == expected

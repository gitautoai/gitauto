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
    log = """Run python -m pytest
=========================== warnings summary ============================
test_example.py::test_warning
  /path/to/file.py:10: DeprecationWarning: deprecated function
    warnings.warn("deprecated function", DeprecationWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== FAILURES ===================================
Test failure details"""

    expected = """Run python -m pytest

=================================== FAILURES ===================================
Test failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_at_start_no_blank_line_added():
    """Test FAILURES section when filtered_lines is empty (line 32 branch coverage)"""
    log = """=========================== test session starts ============================
platform linux -- Python 3.11.4
=================================== FAILURES ===================================
Test failure details"""

    expected = """=================================== FAILURES ===================================
Test failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_after_blank_line():
    """Test FAILURES section when last line is already blank (line 32 branch coverage)"""
    log = """Some content

=========================== test session starts ============================
platform linux -- Python 3.11.4
=================================== FAILURES ===================================
Test failure details"""

    expected = """Some content

=================================== FAILURES ===================================
Test failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_summary_at_start_no_blank_line_added():
    """Test short test summary when filtered_lines is empty (line 41 branch coverage)"""
    log = """=========================== test session starts ============================
platform linux -- Python 3.11.4
=========================== short test summary info ============================
FAILED test_example.py::test_fail"""

    expected = """=========================== short test summary info ============================
FAILED test_example.py::test_fail"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_summary_after_blank_line():
    """Test short test summary when last line is already blank (line 41 branch coverage)"""
    log = """Some content

=========================== test session starts ============================
platform linux -- Python 3.11.4
=========================== short test summary info ============================
FAILED test_example.py::test_fail"""

    expected = """Some content

=========================== short test summary info ============================
FAILED test_example.py::test_fail"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_multiple_sections_combined():
    """Test with all possible sections: test session, warnings, FAILURES, and summary"""
    log = """Initial output
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0
collected 3 items

test_example.py::test_1 PASSED
test_example.py::test_2 FAILED
test_example.py::test_3 PASSED

=========================== warnings summary ============================
test_example.py::test_warning
  DeprecationWarning: deprecated

=================================== FAILURES ===================================
_______________________________ test_2 ________________________________

    def test_2():
>       assert False
E       AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_2 - AssertionError
Final output"""

    expected = """Initial output

=================================== FAILURES ===================================
_______________________________ test_2 ________________________________

    def test_2():
>       assert False
E       AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_2 - AssertionError
Final output"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_test_session_starts():
    """Test with only test session starts section, no FAILURES or summary"""
    log = """Before test
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0
collected 1 items

test_example.py::test_pass PASSED
After test"""

    expected = """Before test
After test"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_warnings_summary():
    """Test with only warnings summary section, no FAILURES or summary"""
    log = """Before warnings
=========================== warnings summary ============================
test_example.py::test_warning
  DeprecationWarning: deprecated function
After warnings"""

    expected = """Before warnings
After warnings"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_none_input():
    """Test with None input to verify decorator handles it"""
    result = remove_pytest_sections(None)
    assert result is None


def test_remove_pytest_sections_partial_markers_not_removed():
    """Test that lines with partial markers (missing ===) are not treated as section markers"""
    log = """test session starts without equals
warnings summary without equals
FAILURES without equals
short test summary info without equals"""

    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_case_sensitive_markers():
    """Test that markers are case-sensitive"""
    log = """=========================== Test Session Starts ============================
Should not be removed
=========================== Warnings Summary ============================
Should not be removed
=========================== failures ===================================
Should not be removed
=========================== Short Test Summary Info ============================
Should not be removed"""

    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_preserves_content_between_sections():
    """Test that content between kept sections is preserved"""
    log = """=========================== test session starts ============================
removed content
=================================== FAILURES ===================================
Failure 1
Some details
More details
=========================== short test summary info ============================
Summary line"""

    expected = """=================================== FAILURES ===================================
Failure 1
Some details
More details

=========================== short test summary info ============================
Summary line"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_no_content_removed_no_blank_line_cleanup():
    """Test that blank lines are not cleaned up when no content is removed"""
    log = """Line 1



Line 2



Line 3"""

    result = remove_pytest_sections(log)
    assert result == log


def test_remove_pytest_sections_multiple_test_sessions():
    """Test with multiple test session starts (edge case)"""
    log = """=========================== test session starts ============================
First session content
=========================== test session starts ============================
Second session content
=================================== FAILURES ===================================
Failure details"""

    expected = """=================================== FAILURES ===================================
Failure details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_multiple_warnings():
    """Test with multiple warnings summary sections (edge case)"""
    log = """=========================== warnings summary ============================
First warning
=========================== warnings summary ============================
Second warning
=================================== FAILURES ===================================
Failure details"""

    expected = """=================================== FAILURES ===================================
Failure details"""

    result = remove_pytest_sections(log)
    assert result == expected

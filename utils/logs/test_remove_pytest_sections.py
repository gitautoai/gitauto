from unittest.mock import patch
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
    log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

/path/to/file.py:20: UserWarning: user warning
  warnings.warn("user warning")

=================================== FAILURES ===================================
Test failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_warnings_summary_only():
    log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

Final content"""

    expected = """Initial content

Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_empty_filtered_lines():
    log = """=========================== test session starts ============================
platform info
=================================== FAILURES ===================================
Test failure content"""

    expected = """=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_blank_last_line():
    log = """Initial content

=========================== test session starts ============================
platform info
=================================== FAILURES ===================================
Test failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
Test failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_empty_filtered_lines():
    log = """=========================== test session starts ============================
platform info
=========================== short test summary info ============================
FAILED test.py::test_example"""

    expected = """=========================== short test summary info ============================
FAILED test.py::test_example"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_blank_last_line():
    log = """Initial content

=========================== test session starts ============================
platform info
=========================== short test summary info ============================
FAILED test.py::test_example"""

    expected = """Initial content

=========================== short test summary info ============================
FAILED test.py::test_example"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_multiple_sections():
    log = """Initial content
=========================== test session starts ============================
platform info
test results
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


def test_remove_pytest_sections_no_content_removal():
    log = """Initial content
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


def test_remove_pytest_sections_only_test_session_starts():
    log = """Initial content
=========================== test session starts ============================
platform info
test results
Final content"""

    expected = """Initial content

Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_partial_markers():
    """Test that partial matches don't trigger section removal"""
    log = """Initial content
=== test session starts but not full marker ===
=== warnings summary but not full marker ===
=== FAILURES but not full marker ===
=== short test summary info but not full marker ===
Final content"""

    expected = """Initial content
=== test session starts but not full marker ===
=== warnings summary but not full marker ===
=== FAILURES but not full marker ===
=== short test summary info but not full marker ===
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_case_sensitivity():
    """Test that markers are case sensitive"""
    log = """Initial content
=========================== TEST SESSION STARTS ============================
=========================== WARNINGS SUMMARY ============================
=================================== failures ===================================
=========================== SHORT TEST SUMMARY INFO ============================
Final content"""

    expected = """Initial content
=========================== TEST SESSION STARTS ============================
=========================== WARNINGS SUMMARY ============================
=================================== failures ===================================
=========================== SHORT TEST SUMMARY INFO ============================
Final content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_exception_handling():
    """Test that exceptions are handled by the decorator"""
    with patch('utils.logs.remove_pytest_sections.re.sub', side_effect=Exception("Test exception")):
        # The decorator should catch the exception and return the default value
        result = remove_pytest_sections("test input")
        assert result == ""


def test_remove_pytest_sections_complex_scenario():
    """Test a complex scenario with all section types and edge cases"""
    log = """Build started
Error in setup

=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /github/workspace
plugins: cov-6.0.0
collecting ... collected 5 items

test_file1.py::test_pass PASSED                                         [ 20%]
test_file1.py::test_fail FAILED                                         [ 40%]
test_file2.py::test_skip SKIPPED                                        [ 60%]
test_file2.py::test_error ERROR                                         [ 80%]
test_file3.py::test_xfail XFAIL                                         [100%]

=========================== warnings summary ============================
test_file1.py::test_pass
  /path/to/file.py:10: DeprecationWarning: deprecated function
    deprecated_function()

test_file2.py::test_skip
  /path/to/file.py:20: UserWarning: user warning
    warnings.warn("user warning")

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_file1.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_file1.py::test_fail - AssertionError
ERROR test_file2.py::test_error - ImportError
SKIPPED test_file2.py::test_skip - reason
XFAIL test_file3.py::test_xfail - expected failure

Build completed with errors"""

    expected = """Build started
Error in setup

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_file1.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_file1.py::test_fail - AssertionError
ERROR test_file2.py::test_error - ImportError
SKIPPED test_file2.py::test_skip - reason
XFAIL test_file3.py::test_xfail - expected failure

Build completed with errors"""

    result = remove_pytest_sections(log)
    assert result == expected

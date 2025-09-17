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


def test_remove_pytest_sections_with_multiple_sections():
    log = """Start content
=========================== test session starts ============================
Session info to be removed
=========================== warnings summary ============================
Warning content to be removed
=================================== FAILURES ===================================
Failure content to keep
=========================== short test summary info ============================
Summary content to keep
End content"""

    expected = """Start content

=================================== FAILURES ===================================
Failure content to keep

=========================== short test summary info ============================
Summary content to keep
End content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_without_prior_content_removal():
    log = """Some content
=================================== FAILURES ===================================
Failure content
More failure content"""

    expected = """Some content
=================================== FAILURES ===================================
Failure content
More failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_without_prior_content_removal():
    log = """Some content
=========================== short test summary info ============================
Summary content
More summary content"""

    expected = """Some content
=========================== short test summary info ============================
Summary content
More summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_blank_line_insertion():
    log = """Content before
=========================== test session starts ============================
Content to remove
=================================== FAILURES ===================================
Failure content"""

    expected = """Content before

=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_blank_line_insertion():
    log = """Content before
=========================== warnings summary ============================
Warning content to remove
=========================== short test summary info ============================
Summary content"""

    expected = """Content before

=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_no_blank_line_when_last_line_is_blank():
    log = """Content before

=========================== test session starts ============================
Content to remove
=================================== FAILURES ===================================
Failure content"""

    expected = """Content before

=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_no_blank_line_when_last_line_is_blank():
    log = """Content before

=========================== warnings summary ============================
Warning content to remove
=========================== short test summary info ============================
Summary content"""

    expected = """Content before

=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_no_blank_line_when_filtered_lines_empty():
    log = """=========================== test session starts ============================
Content to remove
=================================== FAILURES ===================================
Failure content"""

    expected = """=================================== FAILURES ===================================
Failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_no_blank_line_when_filtered_lines_empty():
    log = """=========================== warnings summary ============================
Warning content to remove
=========================== short test summary info ============================
Summary content"""

    expected = """=========================== short test summary info ============================
Summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_lines_with_equals_but_no_keywords():
    log = """Content before
=============== some other section ===============
This should not be removed
=== not a pytest section ===
This should also not be removed
Content after"""

    expected = """Content before
=============== some other section ===============
This should not be removed
=== not a pytest section ===
This should also not be removed
Content after"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_no_excessive_blank_line_cleanup_when_no_content_removed():
    log = """Line 1



Line 2




Line 3"""

    expected = """Line 1



Line 2




Line 3"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_test_session_starts():
    log = """Before content
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
collecting ... collected 2 items
test_example.py::test_pass PASSED
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_warnings_summary():
    log = """Before content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning
  deprecated_function()
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_complex_scenario_with_all_sections():
    log = """Initial log content
Some error occurred
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /github/workspace
plugins: cov-6.0.0
collecting ... collected 5 items

test_file.py::test_one PASSED                                           [ 20%]
test_file.py::test_two FAILED                                           [ 40%]
test_file.py::test_three PASSED                                         [ 60%]
test_file.py::test_four FAILED                                          [ 80%]
test_file.py::test_five PASSED                                          [100%]

=========================== warnings summary ============================
test_file.py::test_two
  /path/to/file.py:15: DeprecationWarning: This is deprecated
    deprecated_function()

test_file.py::test_four
  /path/to/file.py:25: UserWarning: This is a warning
    warnings.warn("This is a warning")

=================================== FAILURES ===================================
________________________________ test_two _________________________________

    def test_two():
>       assert 1 == 2
E       AssertionError

test_file.py:10: AssertionError

________________________________ test_four ________________________________

    def test_four():
>       assert "hello" == "world"
E       AssertionError: assert 'hello' == 'world'

test_file.py:20: AssertionError
=========================== short test summary info ============================
FAILED test_file.py::test_two - AssertionError
FAILED test_file.py::test_four - AssertionError: assert 'hello' == 'world'
========================= 2 failed, 3 passed in 0.50s =========================
Final log content"""

    expected = """Initial log content
Some error occurred

=================================== FAILURES ===================================
________________________________ test_two _________________________________

    def test_two():
>       assert 1 == 2
E       AssertionError

test_file.py:10: AssertionError

________________________________ test_four ________________________________

    def test_four():
>       assert "hello" == "world"
E       AssertionError: assert 'hello' == 'world'

test_file.py:20: AssertionError

=========================== short test summary info ============================
FAILED test_file.py::test_two - AssertionError
FAILED test_file.py::test_four - AssertionError: assert 'hello' == 'world'
========================= 2 failed, 3 passed in 0.50s =========================
Final log content"""

    result = remove_pytest_sections(log)
    assert result == expected

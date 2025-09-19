from unittest.mock import MagicMock, patch
def test_coverage_line_removal():
    """Test that the specific coverage line is removed."""
    from utils.logs.remove_pytest_sections import remove_pytest_sections

    test_log = """Before content
=========================== warnings summary ============================
warning content
Coverage LCOV written to file coverage/lcov.info
=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(test_log)
    expected = """Before content

=========================== short test summary info ============================
summary content"""

    print(f"Result: {repr(result)}")
    print(f"Expected: {repr(expected)}")
    assert result == expected, f"Expected {repr(expected)}, got {repr(result)}"

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
Test failure content here"""

    expected = """Initial content

=================================== FAILURES ===================================
Test failure content here"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_both_test_session_and_warnings():
    log = """Before content
=========================== test session starts ============================
platform info
collected items
=========================== warnings summary ============================
warning content
=================================== FAILURES ===================================
failure content
=========================== short test summary info ============================
summary content"""

    expected = """Before content

=================================== FAILURES ===================================
failure content

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_without_prior_content_removal():
    log = """Some content
=================================== FAILURES ===================================
Test failure details
More failure content"""

    expected = """Some content
=================================== FAILURES ===================================
Test failure details
More failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_without_prior_content_removal():
    log = """Some content
=========================== short test summary info ============================
FAILED test.py::test_function
Summary details"""

    expected = """Some content
=========================== short test summary info ============================
FAILED test.py::test_function
Summary details"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_blank_line_handling():
    log = """Content before
=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
failure content"""

    expected = """Content before

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_failures_with_existing_blank_line():
    log = """Content before

=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
failure content"""

    expected = """Content before

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_blank_line_handling():
    log = """Content before
=========================== test session starts ============================
session content to remove
=========================== short test summary info ============================
summary content"""

    expected = """Content before

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_short_summary_with_existing_blank_line():
    log = """Content before

=========================== test session starts ============================
session content to remove
=========================== short test summary info ============================
summary content"""

    expected = """Content before

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_test_session_starts():
    log = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_only_warnings_summary():
    log = """Before content
=========================== warnings summary ============================
warning 1
warning 2
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_empty_filtered_lines_with_failures():
    log = """=========================== test session starts ============================
session content
=================================== FAILURES ===================================
failure content"""

    expected = """=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_empty_filtered_lines_with_summary():
    log = """=========================== test session starts ============================
session content
=========================== short test summary info ============================
summary content"""

    expected = """=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_no_excessive_blank_lines_when_no_content_removed():
    log = """Line 1




Line 2




Line 3"""

    # Should remain unchanged since no content was removed
    expected = """Line 1




Line 2




Line 3"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_complex_scenario():
    log = """Initial log content
Some error occurred

=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
cachedir: .pytest_cache
rootdir: /workspace
plugins: cov-6.0.0
collecting ... collected 5 items

test_file.py::test_one PASSED                                           [ 20%]
test_file.py::test_two FAILED                                           [ 40%]
test_file.py::test_three PASSED                                         [ 60%]
test_file.py::test_four FAILED                                          [ 80%]
test_file.py::test_five PASSED                                          [100%]

=========================== warnings summary ============================
test_file.py::test_two
  /path/to/file.py:15: DeprecationWarning: deprecated
    deprecated_function()

test_file.py::test_four
  /path/to/file.py:25: UserWarning: warning message
    warnings.warn("warning message")

=================================== FAILURES ===================================
__________________________ test_two __________________________

    def test_two():
>       assert False, "This should fail"
E       AssertionError: This should fail

test_file.py:10: AssertionError

__________________________ test_four __________________________

    def test_four():
>       assert 1 == 2
E       assert 1 == 2

test_file.py:20: AssertionError
=========================== short test summary info ============================
FAILED test_file.py::test_two - AssertionError: This should fail
FAILED test_file.py::test_four - assert 1 == 2

Final log content"""

    expected = """Initial log content
Some error occurred

=================================== FAILURES ===================================
__________________________ test_two __________________________

    def test_two():
>       assert False, "This should fail"
E       AssertionError: This should fail

test_file.py:10: AssertionError

__________________________ test_four __________________________

    def test_four():
>       assert 1 == 2
E       assert 1 == 2

test_file.py:20: AssertionError

=========================== short test summary info ============================
FAILED test_file.py::test_two - AssertionError: This should fail
FAILED test_file.py::test_four - assert 1 == 2

Final log content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_exception_handling():
    """Test that the function handles exceptions and returns default value."""
    # Test with a function that would cause an exception if not handled
    with patch('utils.logs.remove_pytest_sections.re.sub') as mock_re_sub:
        # Make re.sub raise an exception
        mock_re_sub.side_effect = Exception("Test exception")

        # The function should still return the default value due to the decorator
        result = remove_pytest_sections("test content with session starts")

        # Due to the handle_exceptions decorator, it should return the default value ""
        assert result == ""


def test_remove_pytest_sections_with_falsy_values():
    """Test function behavior with various falsy values."""
    # Test with None
    assert remove_pytest_sections(None) is None

    # Test with empty string
    assert remove_pytest_sections("") == ""

    # Test with False (though not typical input, should be handled)
    assert remove_pytest_sections(False) is False

def test_remove_pytest_sections_with_coverage_line():
    """Test that coverage lines are properly removed."""
    log = """Initial content
=========================== warnings summary ============================
warning content
Coverage LCOV written to file coverage/lcov.info
=========================== short test summary info ============================
summary content"""

    expected = """Initial content

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_with_coverage_line_after_session():
    """Test that coverage lines are properly removed when they appear after test session."""
    log = """Initial content
=========================== test session starts ============================
platform info
collected items

def test_remove_pytest_sections_real_world_scenario():
    """Test with a real-world scenario similar to the failing test."""
    log = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
=========================== test session starts ============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
plugins: cov-6.0.0, anyio-4.4.0, Faker-24.14.1, asyncio-0.26.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

test results here

=============================== warnings summary ===============================
some warnings

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------- coverage: platform linux, python 3.12.11-final-0 ----------
Coverage LCOV written to file coverage/lcov.info

=================================== FAILURES ===================================
failure content
=========================== short test summary info ============================
summary content"""


def test_remove_pytest_sections_with_coverage_section():
    """Test that coverage sections with dashes are properly removed."""
    log = """Some content
=========================== warnings summary ============================
warning content

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------- coverage: platform linux, python 3.12.11-final-0 ----------
Coverage LCOV written to file coverage/lcov.info

=========================== short test summary info ============================
summary content"""

    expected = """Some content

=========================== short test summary info ============================
summary content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_coverage_section_only():
    """Test that standalone coverage sections are properly removed."""
    log = """Before content
---------- coverage: platform linux, python 3.12.11-final-0 ----------
Coverage LCOV written to file coverage/lcov.info
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    assert result == expected


def test_remove_pytest_sections_docs_line():
    """Test that docs lines are properly removed."""
    log = """Before content
=========================== warnings summary ============================
warning content
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)

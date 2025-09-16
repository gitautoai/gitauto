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

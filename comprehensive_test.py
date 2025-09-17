from utils.logs.remove_pytest_sections import remove_pytest_sections
from config import UTF8

def test_none_input():
    result = remove_pytest_sections(None)
    print("None input test:", result is None)
    return result is None

def test_empty_input():
    result = remove_pytest_sections("")
    print("Empty input test:", result == "")
    return result == ""

def test_basic_functionality():
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
    match = result == expected
    print("Basic functionality test:", match)
    if not match:
        print("Result:")
        print(repr(result))
        print("\nExpected:")
        print(repr(expected))
    return match

def test_actual_payload():
    try:
        with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
            original_log = f.read()

        with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
            expected_output = f.read()

        result = remove_pytest_sections(original_log)
        match = result == expected_output
        print("Actual payload test:", match)
        return match
    except Exception as e:
        print("Actual payload test failed with exception:", e)
        return False

if __name__ == "__main__":
    tests = [test_none_input, test_empty_input, test_basic_functionality, test_actual_payload]
    results = [test() for test in tests]
    print(f"\nOverall: {sum(results)}/{len(results)} tests passed")

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Simple test case
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
print("RESULT:")
print(repr(result))
print("\nEXPECTED:")
print(repr(expected))
print("\nMATCH:", result == expected)

if result != expected:
    print("\nDIFFERENCES:")
    result_lines = result.split('\n')
    expected_lines = expected.split('\n')
    for i, (r, e) in enumerate(zip(result_lines, expected_lines)):
        if r != e:
            print(f"Line {i}: Got {repr(r)}, Expected {repr(e)}")
    if len(result_lines) != len(expected_lines):
        print(f"Length difference: Got {len(result_lines)}, Expected {len(expected_lines)}")

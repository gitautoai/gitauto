from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test case 1: warnings summary only
test_input1 = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

Final content"""

expected1 = """Initial content

Final content"""

result1 = remove_pytest_sections(test_input1)
print("TEST 1 - Warnings summary only:")
print("Expected:")
print(repr(expected1))
print("Got:")
print(repr(result1))
print("Match:", result1 == expected1)
print("=" * 50)

# Test case 2: test session starts
test_input2 = """Run python -m pytest
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
plugins: cov-6.0.0, anyio-4.4.0, Faker-24.14.1, asyncio-0.26.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

self = <test_should_test_file.TestShouldTestFile object at 0x7f44e0106780>

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
Error: Process completed with exit code 1."""

expected2 = """Run python -m pytest

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

self = <test_should_test_file.TestShouldTestFile object at 0x7f44e0106780>

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
Error: Process completed with exit code 1."""

result2 = remove_pytest_sections(test_input2)
print("TEST 2 - Test session starts:")
print("Expected:")
print(repr(expected2))
print("Got:")
print(repr(result2))
print("Match:", result2 == expected2)
print("=" * 50)

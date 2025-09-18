from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with a simple example
test_input = """Run python -m pytest
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

result = remove_pytest_sections(test_input)
print("RESULT:")
print(result)
print("=" * 50)

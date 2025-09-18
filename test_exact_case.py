from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with the exact failing case
test_input = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
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

expected = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))

=================================== FAILURES ===================================
_____ TestShouldTestFile.test_should_test_file_with_boolean_return_values ______

self = <test_should_test_file.TestShouldTestFile object at 0x7f44e0106780>

=========================== short test summary info ============================
FAILED utils/files/test_should_test_file.py::TestShouldTestFile::test_should_test_file_with_boolean_return_values - assert False
Error: Process completed with exit code 1."""

result = remove_pytest_sections(test_input)
print("RESULT:")
print(repr(result))
print("\nEXPECTED:")
print(repr(expected))
print("\nMATCH:", result == expected)

# Check the specific line that should trigger removal
test_line = "============================= test session starts =============================="
print(f"\nTest line: {repr(test_line)}")
print(f"'===' in line: {'===' in test_line}")
print(f"'test session starts' in line: {'test session starts' in test_line}")
print(f"Both conditions: {'===' in test_line and 'test session starts' in test_line}")

if result != expected:
    print("\nDIFFERENCES:")
    result_lines = result.split('\n')
    expected_lines = expected.split('\n')
    max_len = max(len(result_lines), len(expected_lines))
    for i in range(max_len):
        r = result_lines[i] if i < len(result_lines) else "<MISSING>"
        e = expected_lines[i] if i < len(expected_lines) else "<MISSING>"
        if r != e:
            print(f"Line {i}: Got {repr(r)}, Expected {repr(e)}")
    print(f"Result length: {len(result_lines)}, Expected length: {len(expected_lines)}")

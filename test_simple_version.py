from utils.logs.remove_pytest_sections_simple import remove_pytest_sections

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

# Check specific lines
problematic_lines = [
    "asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function",
    "collected 2900 items"
]

for line in problematic_lines:
    print(f"\nLine: {repr(line)}")
    print(f"In result: {line in result}")
    print(f"In expected: {line in expected}")

# Test the session detection
session_line = "============================= test session starts =============================="
print(f"\nSession line: {repr(session_line)}")
print(f"In input: {session_line in test_input}")
print(f"In result: {session_line in result}")
print(f"In expected: {session_line in expected}")

# Manual check
lines = test_input.split('\n')
for i, line in enumerate(lines):
    if 'test session starts' in line:
        print(f"Found session line at index {i}: {repr(line)}")
        print(f"'===' in line: {'===' in line}")
        print(f"'test session starts' in line: {'test session starts' in line}")
        break

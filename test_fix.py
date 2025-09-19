#!/usr/bin/env python3

from utils.logs.clean_logs import clean_logs

# Test the exact scenario from the failing test
test_log = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
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
summary content
Error: Process completed with exit code 1."""

result = clean_logs(test_log)
print("Result:")
print(repr(result))

expected = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))

=================================== FAILURES ===================================
failure content

=========================== short test summary info ============================
summary content
Error: Process completed with exit code 1."""

print("\nExpected:")
print(repr(expected))
print(f"\nMatch: {result == expected}")

# Test just the coverage line
from utils.logs.remove_pytest_sections import remove_pytest_sections

coverage_test = """Before
---------- coverage: platform linux, python 3.12.11-final-0 ----------
Coverage LCOV written to file coverage/lcov.info
After"""

coverage_result = remove_pytest_sections(coverage_test)
print(f"\nCoverage test result: {repr(coverage_result)}")
print(f"Expected: {repr('Before\\nAfter')}")
print(f"Coverage test match: {coverage_result == 'Before\\nAfter'}")

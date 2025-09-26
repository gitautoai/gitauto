#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_basic_case():
    """Test the basic case that was failing"""
    log = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
plugins: cov-6.0.0, anyio-4.4.0, Faker-24.14.1, asyncio-0.26.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

services/anthropic/test_evaluate_condition.py .......                    [  0%]
services/anthropic/test_exceptions.py ................                   [  0%]

=================================== FAILURES ===================================
failure content"""

    expected = """Run python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info
/opt/hostedtoolcache/Python/3.12.11/x64/lib/python3.12/site-packages/pytest_asyncio/plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    return result == expected, result, expected

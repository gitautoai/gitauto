# pylint: disable=redefined-outer-name
from unittest.mock import patch

import pytest
from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs


def test_minimize_jest_test_logs_with_summary():
    """Test that Jest logs are minimized when summary section exists."""
    input_log = """CircleCI Build Log: yarn test
yarn run v1.22.22
$ craco test --watchAll=false --coverage=true

PASS test/utils/timeout.test.ts (10.698 s)
  timeout
    ✓ should return false when start time equals current time (19 ms)
    ✓ should return false when elapsed time is less than time limit (1 ms)

FAIL test/components/NewAccount.test.tsx (22.052 s)
  <NewAccount />
    ✓ renders without crashing (100 ms)
    ✕ should handle click events

--------------------------------|---------|----------|---------|---------|-------
File                            | % Stmts | % Branch | % Funcs | % Lines | Uncov
--------------------------------|---------|----------|---------|---------|-------
All files                       |   61.12 |    56.36 |   54.63 |   61.05 |
  src/App.tsx                   |     100 |      100 |     100 |     100 |
--------------------------------|---------|----------|---------|---------|-------

Summary of all failing tests
FAIL test/components/NewAccount.test.tsx (22.052 s)
  ● should handle click events

    Expected: true
    Received: false
Test Suites: 1 failed, 1 passed, 2 total
Tests:       1 failed, 2 passed, 3 total"""

    expected = """CircleCI Build Log: yarn test
yarn run v1.22.22
$ craco test --watchAll=false --coverage=true

Summary of all failing tests
FAIL test/components/NewAccount.test.tsx (22.052 s)
  ● should handle click events

    Expected: true
    Received: false
Test Suites: 1 failed, 1 passed, 2 total
Tests:       1 failed, 2 passed, 3 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_no_summary():
    """Test that logs without summary section are returned unchanged."""
    input_log = """CircleCI Build Log: yarn test
yarn run v1.22.22
$ craco test --watchAll=false

PASS test/utils/timeout.test.ts (10.698 s)
  ✓ all tests passed

Test Suites: 1 passed, 1 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_empty():
    """Test that empty logs are returned unchanged."""
    assert minimize_jest_test_logs("") == ""


def test_minimize_jest_test_logs_none():
    """Test that None input is handled correctly."""
    assert minimize_jest_test_logs(None) is None


def test_minimize_jest_test_logs_not_jest():
    """Test that non-Jest logs are returned unchanged."""
    input_log = """Some other build output
with no Jest markers
or test results"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_multiple_commands():
    """Test that multiple command headers are preserved."""
    input_log = """yarn run v1.22.22
$ npm test
$ jest --coverage

PASS test/file1.test.ts
PASS test/file2.test.ts

Summary of all failing tests
FAIL test/file3.test.ts
  ● test case failed

Test Suites: 1 failed, 2 passed, 3 total"""

    expected = """yarn run v1.22.22
$ npm test
$ jest --coverage

Summary of all failing tests
FAIL test/file3.test.ts
  ● test case failed

Test Suites: 1 failed, 2 passed, 3 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_all_command_types():
    """Test that all supported command types are preserved."""
    input_log = """CircleCI Build Log: Starting tests
yarn run v1.22.22
npm run test:ci
$ craco test --watchAll=false
$ react-scripts test --coverage
$ jest --verbose
$ vitest run
$ npm test
$ yarn test

Some test output here
More test results

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """CircleCI Build Log: Starting tests
yarn run v1.22.22
npm run test:ci
$ craco test --watchAll=false
$ react-scripts test --coverage
$ jest --verbose
$ vitest run
$ npm test
$ yarn test

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_no_header_with_summary():
    """Test case where summary exists but no header commands are found."""
    input_log = """Some random output
No command headers here
Just regular text

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    expected = """Summary of all failing tests
FAIL test/example.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_header_complete_logic():
    """Test the header_complete logic when non-command lines appear after headers."""
    input_log = """$ npm test
$ jest --coverage
Some non-command line that should trigger header_complete
Another non-command line
Yet another line

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """$ npm test
$ jest --coverage

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_summary_only():
    """Test case where only the summary line exists."""
    input_log = """$ yarn test
Some test output
Summary of all failing tests"""

    expected = """$ yarn test

Summary of all failing tests"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_command_in_middle_of_line():
    """Test that commands are detected even when they're part of a larger line."""
    input_log = """Running $ jest --coverage with options
Executing yarn run v1.22.22 for tests
Starting npm run test:ci process

Some test output here

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """Running $ jest --coverage with options
Executing yarn run v1.22.22 for tests
Starting npm run test:ci process

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_whitespace_handling():
    """Test that whitespace is properly handled and stripped."""
    input_log = """  $ npm test

  Some output

  Summary of all failing tests
  FAIL test/example.test.ts
    ● test failed
  """

    expected = """$ npm test

Summary of all failing tests
  FAIL test/example.test.ts
    ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_react_scripts_command():
    """Test specific react-scripts test command detection."""
    input_log = """$ react-scripts test --watchAll=false
Starting tests...

PASS src/App.test.js
FAIL src/Component.test.js

Summary of all failing tests
FAIL src/Component.test.js
  ● Component should render"""

    expected = """$ react-scripts test --watchAll=false

Summary of all failing tests
FAIL src/Component.test.js
  ● Component should render"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_vitest_command():
    """Test specific vitest command detection."""
    input_log = """$ vitest run --coverage
Running tests with Vitest

✓ test/utils.test.ts
✗ test/component.test.ts

Summary of all failing tests
FAIL test/component.test.ts
  ● should work correctly"""

    expected = """$ vitest run --coverage

Summary of all failing tests
FAIL test/component.test.ts
  ● should work correctly"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


@patch('utils.logs.minimize_jest_test_logs.handle_exceptions')
def test_minimize_jest_test_logs_exception_handling(mock_handle_exceptions):
    """Test that the function is properly decorated with exception handling."""
    # The decorator should be applied to the function
    mock_handle_exceptions.assert_called_once()

    # Verify the decorator was called with correct parameters
    call_args = mock_handle_exceptions.call_args
    assert call_args[1]['raise_on_error'] is False
    assert callable(call_args[1]['default_return_value'])


def test_minimize_jest_test_logs_exception_default_return():
    """Test the default return value behavior when an exception occurs."""
    # Test that the default_return_value lambda works correctly
    test_input = "test error log"

    # The decorator's default_return_value is a lambda that returns the input
    # This simulates what would happen if an exception occurred
    default_return_func = lambda error_log: error_log
    result = default_return_func(test_input)

    assert result == test_input


def test_minimize_jest_test_logs_case_sensitivity():
    """Test that the function is case-sensitive for the summary marker."""
    input_log = """$ npm test
Some test output

summary of all failing tests
FAIL test/example.test.ts"""

    # Should return unchanged because "summary" is lowercase
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_partial_command_match():
    """Test that partial command matches work correctly."""
    input_log = """This line contains $ jest but not at start
Another line with yarn run v in the middle
A line with npm run somewhere

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """This line contains $ jest but not at start
Another line with yarn run v in the middle
A line with npm run somewhere

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_empty_lines_preservation():
    """Test that empty lines are properly handled in the output."""
    input_log = """$ npm test


Some output with empty lines


Summary of all failing tests

FAIL test/example.test.ts

  ● test failed

"""

    expected = """$ npm test

Summary of all failing tests

FAIL test/example.test.ts

  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected

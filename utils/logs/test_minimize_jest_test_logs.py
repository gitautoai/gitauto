from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs


def test_minimize_jest_test_logs_with_summary():
    """Test that Jest logs are minimized when summary section exists."""
    input_log = """```CircleCI Build Log: yarn test
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

    expected = """```CircleCI Build Log: yarn test
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
    input_log = """```CircleCI Build Log: yarn test
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
    """Test that None input is handled gracefully by decorator."""
    result = minimize_jest_test_logs(None)
    assert result is None


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


def test_minimize_jest_test_logs_with_header_only_no_summary():
    """Test logs with header commands but no summary - covers uncovered branch at line 20."""
    input_log = """CircleCI Build Log
yarn run v1.22.22
$ jest --coverage

PASS test/file1.test.ts
PASS test/file2.test.ts

Test Suites: 2 passed, 2 total
Tests: 10 passed, 10 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_all_command_variations():
    """Test that all supported command variations are preserved."""
    input_log = """CircleCI Build Log
yarn run v1.22.22
npm run test
$ craco test
$ react-scripts test
$ jest
$ vitest
$ npm test
$ yarn test

Some test output here

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """CircleCI Build Log
yarn run v1.22.22
npm run test
$ craco test
$ react-scripts test
$ jest
$ vitest
$ npm test
$ yarn test

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_summary_at_beginning():
    """Test when summary appears at the very beginning."""
    input_log = """Summary of all failing tests
FAIL test/example.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    expected = """
Summary of all failing tests
FAIL test/example.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_summary_with_no_header():
    """Test when summary exists but no header commands."""
    input_log = """Some random output
More random output

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """
Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_with_single_line():
    """Test with single line containing summary."""
    input_log = "Summary of all failing tests"
    expected = "\nSummary of all failing tests"

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_whitespace_only():
    """Test with whitespace-only input."""
    input_log = "   \n\n   \n"
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_summary_in_middle_with_content_after():
    """Test that everything after summary is preserved."""
    input_log = """$ jest

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test case 1 failed
  ● test case 2 failed

Additional error details
Stack trace information
More debugging info"""

    expected = """$ jest

Summary of all failing tests
FAIL test/file2.test.ts
  ● test case 1 failed
  ● test case 2 failed

Additional error details
Stack trace information
More debugging info"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_partial_command_match():
    """Test that partial command matches work correctly."""
    input_log = """Running yarn run v1.22.22 in CI
Executing $ npm test --coverage

Test output here

Summary of all failing tests
FAIL test/example.test.ts"""

    expected = """Running yarn run v1.22.22 in CI
Executing $ npm test --coverage

Summary of all failing tests
FAIL test/example.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_case_sensitive_summary():
    """Test that summary detection is case-sensitive."""
    input_log = """$ jest

FAIL test/example.test.ts

summary of all failing tests
This should not trigger the summary detection"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_empty_lines_preserved():
    """Test that empty lines in summary section are preserved."""
    input_log = """$ jest

Test output

Summary of all failing tests

FAIL test/example.test.ts

  ● test failed

Test Suites: 1 failed"""

    expected = """$ jest

Summary of all failing tests

FAIL test/example.test.ts

  ● test failed

Test Suites: 1 failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_only_header_commands():
    """Test with only header commands and no other content."""
    input_log = """CircleCI Build Log
yarn run v1.22.22
$ jest"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_vitest_command():
    """Test with vitest command specifically."""
    input_log = """$ vitest run

Running tests...

Summary of all failing tests
FAIL test/example.test.ts
  ● vitest test failed"""

    expected = """$ vitest run

Summary of all failing tests
FAIL test/example.test.ts
  ● vitest test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_react_scripts_command():
    """Test with react-scripts test command."""
    input_log = """$ react-scripts test --coverage

Test results...

Summary of all failing tests
FAIL test/App.test.tsx"""

    expected = """$ react-scripts test --coverage

Summary of all failing tests
FAIL test/App.test.tsx"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_mixed_content_before_summary():
    """Test with mixed content including commands and non-commands before summary."""
    input_log = """CircleCI Build Log
yarn run v1.22.22
$ jest

Random test output line 1
Random test output line 2
Random test output line 3

Summary of all failing tests
FAIL test/example.test.ts"""

    expected = """CircleCI Build Log
yarn run v1.22.22
$ jest

Summary of all failing tests
FAIL test/example.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_newline_variations():
    """Test with various newline patterns."""
    input_log = "$ jest\n\n\n\nSummary of all failing tests\nFAIL test/example.test.ts"
    expected = "$ jest\n\nSummary of all failing tests\nFAIL test/example.test.ts"

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_header_complete_flag():
    """Test that header_complete flag logic works correctly."""
    input_log = """$ jest
Some non-command line after header
Another non-command line

Summary of all failing tests
FAIL test/example.test.ts"""

    expected = """$ jest

Summary of all failing tests
FAIL test/example.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_no_header_no_summary():
    """Test with neither header commands nor summary."""
    input_log = """Just some random text
No commands here
No summary either"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_summary_keyword_in_other_context():
    """Test that summary keyword in different context doesn't trigger minimization."""
    input_log = """$ jest

This is a summary of something else
Not the failing tests summary

Test Suites: 1 passed"""

    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_multiple_summary_occurrences():
    """Test behavior when summary text appears multiple times."""
    input_log = """$ jest

Some text mentioning Summary of all failing tests in a comment

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    expected = """$ jest

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    # Should find the first occurrence
    assert result == expected


def test_minimize_jest_test_logs_ansi_escape_codes():
    """Test with ANSI escape codes in the log."""
    input_log = """[2K[1G[1myarn run v1.22.22[22m
[2K[1G[2m$ craco test[22m

PASS test/file.test.ts

Summary of all failing tests
FAIL test/example.test.ts"""

    expected = """[2K[1G[1myarn run v1.22.22[22m
[2K[1G[2m$ craco test[22m

Summary of all failing tests
FAIL test/example.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_very_long_log():
    """Test with a very long log to ensure performance."""
    # Create a log with many test results
    header = "$ jest\n\n"
    test_output = "\n".join([f"PASS test/file{i}.test.ts" for i in range(100)])
    summary = "\n\nSummary of all failing tests\nFAIL test/example.test.ts"
    input_log = header + test_output + summary

    expected = header + summary

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_special_characters():
    """Test with special characters in the log."""
    input_log = """$ jest

Test output with special chars: @#$%^&*()

Summary of all failing tests
FAIL test/example.test.ts
  ● Error: Expected "foo" but got "bar"
  ● Stack trace with special chars: /path/to/file.ts:123:45"""

    expected = """$ jest

Summary of all failing tests
FAIL test/example.test.ts
  ● Error: Expected "foo" but got "bar"
  ● Stack trace with special chars: /path/to/file.ts:123:45"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_unicode_characters():
    """Test with unicode characters in the log."""
    input_log = """$ jest

Test output with unicode: ✓ ✕ ●

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed ✕"""

    expected = """$ jest

Summary of all failing tests
FAIL test/example.test.ts
  ● test failed ✕"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected

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


def test_minimize_jest_test_logs_header_complete_branch():
    """Test the branch where header is complete but no summary is found.

    This covers the uncovered branch at line 42-44 where:
    - result_lines has content (header lines were found)
    - A non-command, non-summary line is encountered after header lines
    - header_complete becomes True
    - But no summary section is found in the entire log

    The key is having: header command -> non-command line -> rest of log without summary
    """
    input_log = """yarn run v1.22.22
Some non-command line that triggers header_complete
$ npm test

PASS test/file1.test.ts
PASS test/file2.test.ts
FAIL test/file3.test.ts

Test Suites: 1 failed, 2 passed, 3 total"""

    # Should return unchanged since no summary section exists
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_header_complete_branch_explicit():
    """Explicit test for the header_complete branch (line 42-44).

    This test ensures the elif branch at line 42-44 is executed:
    - First line is a command (adds to result_lines)
    - Second line is NOT a command and NOT summary (triggers elif at line 42)
    - No summary section exists in the log
    """
    input_log = """$ jest
This line is not a command
PASS test/file1.test.ts
Test Suites: 1 passed, 1 total"""

    # Should return unchanged since no summary section exists
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_summary_at_beginning():
    """Test when summary section appears at the very beginning."""
    input_log = """Summary of all failing tests
FAIL test/file1.test.ts
  ● test case failed

Test Suites: 1 failed, 1 total"""

    expected = """
Summary of all failing tests
FAIL test/file1.test.ts
  ● test case failed

Test Suites: 1 failed, 1 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_vitest_command():
    """Test with vitest command."""
    input_log = """$ vitest run --coverage

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """$ vitest run --coverage

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_react_scripts_command():
    """Test with react-scripts test command."""
    input_log = """$ react-scripts test --coverage

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """$ react-scripts test --coverage

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_yarn_test_command():
    """Test with yarn test command."""
    input_log = """$ yarn test --watchAll=false

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """$ yarn test --watchAll=false

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_npm_run_command():
    """Test with npm run command."""
    input_log = """npm run test:coverage

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """npm run test:coverage

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_circleci_build_log():
    """Test with CircleCI Build Log header."""
    input_log = """CircleCI Build Log: npm test

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """CircleCI Build Log: npm test

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_summary_with_no_content_after():
    """Test when summary section is at the end with no additional content."""
    input_log = """yarn run v1.22.22
$ jest

PASS test/file1.test.ts

Summary of all failing tests"""

    expected = """yarn run v1.22.22
$ jest

Summary of all failing tests"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_multiple_command_occurrences():
    """Test with multiple occurrences of command keywords in different contexts."""
    input_log = """yarn run v1.22.22
$ npm test
Running jest tests...
$ jest --coverage
Some output mentioning $ jest again

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """yarn run v1.22.22
$ npm test
$ jest --coverage

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_only_summary_no_header():
    """Test when there's only summary section without any header commands."""
    input_log = """Some random output
More random output

Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    expected = """
Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed

Test Suites: 1 failed, 1 total"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_whitespace_handling():
    """Test proper handling of whitespace and blank lines."""
    input_log = """yarn run v1.22.22


$ jest --coverage


PASS test/file1.test.ts


Summary of all failing tests
FAIL test/file2.test.ts"""

    expected = """yarn run v1.22.22
$ jest --coverage

Summary of all failing tests
FAIL test/file2.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_all_commands():
    """Test with all supported command types."""
    input_log = """CircleCI Build Log: test suite
yarn run v1.22.22
npm run test
$ craco test
$ react-scripts test
$ jest
$ vitest
$ npm test
$ yarn test

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    expected = """CircleCI Build Log: test suite
yarn run v1.22.22
npm run test
$ craco test
$ react-scripts test
$ jest
$ vitest
$ npm test
$ yarn test

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_summary_keyword_in_middle():
    """Test when 'Summary of all failing tests' appears in the middle of output."""
    input_log = """yarn run v1.22.22
$ jest

PASS test/file1.test.ts
FAIL test/file2.test.ts

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed

Additional output after summary
More output here"""

    expected = """yarn run v1.22.22
$ jest

Summary of all failing tests
FAIL test/file2.test.ts
  ● test failed

Additional output after summary
More output here"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_exception_handling():
    """Test that exceptions are handled gracefully by the decorator."""
    # The decorator should catch any exceptions and return the input unchanged
    # Testing with various edge cases that might cause issues

    # Test with very long string
    long_log = "x" * 100000 + "\nSummary of all failing tests\nFAIL test"
    result = minimize_jest_test_logs(long_log)
    assert "Summary of all failing tests" in result

    # Test with special characters
    special_log = """$ jest
Special chars: \t\r\n\x00
Summary of all failing tests
FAIL test"""
    result = minimize_jest_test_logs(special_log)
    assert "Summary of all failing tests" in result


def test_minimize_jest_test_logs_case_sensitive():
    """Test that the function is case-sensitive for the summary keyword."""
    input_log = """yarn run v1.22.22
$ jest

PASS test/file1.test.ts

SUMMARY OF ALL FAILING TESTS
FAIL test/file2.test.ts"""

    # Should return unchanged because the summary keyword is case-sensitive
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_partial_summary_keyword():
    """Test that partial matches of summary keyword don't trigger minimization."""
    input_log = """yarn run v1.22.22
$ jest

PASS test/file1.test.ts

Summary of failing tests
FAIL test/file2.test.ts"""

    # Should return unchanged because it's not the exact keyword
    result = minimize_jest_test_logs(input_log)
    assert result == input_log


def test_minimize_jest_test_logs_no_header_with_summary():
    """Test when summary exists but no header commands are present."""
    input_log = """Random output line 1
Random output line 2
Random output line 3

Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed"""

    expected = """
Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_header_then_non_command_then_summary():
    """Test header -> non-command line -> summary pattern.

    This ensures the header_complete flag works correctly when
    summary appears after non-command lines.
    """
    input_log = """$ jest
Non-command line here
Another non-command line
Summary of all failing tests
FAIL test/file1.test.ts"""

    expected = """$ jest

Summary of all failing tests
FAIL test/file1.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_empty_lines_only():
    """Test with only empty lines and summary."""
    input_log = """

Summary of all failing tests
FAIL test/file1.test.ts"""

    expected = """
Summary of all failing tests
FAIL test/file1.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_command_after_non_command():
    """Test when command appears after non-command lines.

    This tests that once header_complete is True, subsequent command
    lines are not added to result_lines.
    """
    input_log = """$ jest
Non-command line
$ npm test
More output
Summary of all failing tests
FAIL test/file1.test.ts"""

    expected = """$ jest

Summary of all failing tests
FAIL test/file1.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_unicode_characters():
    """Test with unicode characters in the log."""
    input_log = """$ jest
Test with unicode: ✓ ✗ ● ◯ 🎉

Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed with emoji 🔥"""

    expected = """$ jest

Summary of all failing tests
FAIL test/file1.test.ts
  ● test failed with emoji 🔥"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected


def test_minimize_jest_test_logs_newline_variations():
    """Test with different newline variations."""
    # Test with \r\n (Windows style)
    input_log = "$ jest\r\nPASS test\r\n\r\nSummary of all failing tests\r\nFAIL test"
    result = minimize_jest_test_logs(input_log)
    assert "Summary of all failing tests" in result
    assert "$ jest" in result


def test_minimize_jest_test_logs_summary_as_substring():
    """Test when summary keyword appears as part of another string."""
    input_log = """$ jest
This is not a Summary of all failing tests line
PASS test/file1.test.ts

Summary of all failing tests
FAIL test/file2.test.ts"""

    expected = """$ jest

Summary of all failing tests
FAIL test/file2.test.ts"""

    result = minimize_jest_test_logs(input_log)
    assert result == expected

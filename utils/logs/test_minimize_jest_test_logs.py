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
    assert minimize_jest_test_logs("") == ""


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

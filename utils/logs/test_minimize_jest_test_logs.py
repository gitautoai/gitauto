import os

from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


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

    result = minimize_jest_test_logs(input_log)
    assert "```CircleCI Build Log: yarn test" in result
    assert "Summary of all failing tests" in result
    assert "● should handle click events" in result
    assert "Expected: true" in result
    assert "Test Suites: 1 failed, 1 passed, 2 total" in result
    # Coverage table and PASS sections should be removed
    assert "% Stmts" not in result
    assert "PASS test/utils/timeout" not in result


def test_minimize_jest_test_logs_no_summary_still_minimizes():
    """Test that logs without summary section still get minimized via strip_jest_noise."""
    input_log = (
        "yarn run v1.22.22\n"
        '{"level":"debug","msg":"connecting"}\n'
        '{"level":"debug","msg":"query"}\n'
        "FAIL src/a.test.ts\n"
        "  ✕ should work\n"
        "\n"
        "  ● should work\n"
        "\n"
        "    expect(true).toBe(false)\n"
        "\n"
        "      at Object.<anonymous> (node_modules/jest/build/index.js:100:10)\n"
        "      at Object.<anonymous> (src/a.test.ts:5:3)\n"
        "\n"
        "PASS src/b.test.ts\n"
        "  ✓ should pass (1 ms)\n"
        "Test Suites: 1 failed, 1 passed, 2 total\n"
        "Tests: 1 failed, 1 passed, 2 total"
    )
    result = minimize_jest_test_logs(input_log)
    # strip_jest_noise removes JSON lines, ✓, PASS section
    # strip_node_modules removes node_modules/jest stack frame
    # dedup_jest_errors drops ✕ line (between FAIL and ●), keeps ● block
    expected = (
        "yarn run v1.22.22\n"
        "FAIL src/a.test.ts\n"
        "  ● should work\n"
        "\n"
        "    expect(true).toBe(false)\n"
        "\n"
        "      at Object.<anonymous> (src/a.test.ts:5:3)\n"
        "\n"
        "\n"
        "Test Suites: 1 failed, 1 passed, 2 total\n"
        "Tests: 1 failed, 1 passed, 2 total"
    )
    assert result == expected


def test_minimize_jest_test_logs_empty():
    assert minimize_jest_test_logs("") == ""


def test_minimize_jest_test_logs_plain_text_preserved():
    """Test that plain text without noise is preserved."""
    input_log = "Some other build output\nwith no Jest markers\nor test results"
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

    result = minimize_jest_test_logs(input_log)
    assert "yarn run v1.22.22" in result
    assert "$ jest --coverage" in result
    assert "Summary of all failing tests" in result
    assert "● test case failed" in result
    assert "Test Suites: 1 failed, 2 passed, 3 total" in result
    # PASS sections should be removed
    assert "PASS test/file1" not in result


def test_minimize_real_subprocess_fixture():
    """Test full pipeline on real 776K jest subprocess output from production."""
    fixture_path = os.path.join(FIXTURES_DIR, "raw_jest_subprocess_output.txt")
    expected_path = os.path.join(
        FIXTURES_DIR, "raw_jest_subprocess_output_minimized.txt"
    )

    with open(fixture_path, encoding="utf-8") as f:
        raw = f.read()
    with open(expected_path, encoding="utf-8") as f:
        expected = f.read()

    result = minimize_jest_test_logs(raw)
    assert result == expected.strip()

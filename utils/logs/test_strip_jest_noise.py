import os

from utils.logs.strip_jest_noise import strip_jest_noise

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_strip_jest_noise_removes_json_debug_lines():
    log = 'FAIL src/test.ts\n{"level":"debug","msg":"connecting"}\n  ✕ should work\nerror Command failed'
    result = strip_jest_noise(log)
    assert '{"level":"debug"' not in result
    assert "FAIL src/test.ts" in result
    assert "should work" in result


def test_strip_jest_noise_removes_passing_test_lines():
    log = "FAIL src/test.ts\n  ✕ should fail\n  ✓ should pass (1 ms)\nerror"
    result = strip_jest_noise(log)
    assert "✓" not in result
    assert "✕" in result


def test_strip_jest_noise_removes_pass_sections():
    log = "FAIL src/a.test.ts\n  ✕ broken\nPASS src/b.test.ts\n  describe block\n    nested\nTest Suites: 1 failed"
    result = strip_jest_noise(log)
    assert "PASS src/b.test.ts" not in result
    assert "describe block" not in result
    assert "FAIL src/a.test.ts" in result
    assert "Test Suites: 1 failed" in result


def test_strip_jest_noise_removes_mongodb_download():
    log = 'Downloading MongoDB "7.0.0": 100% (80.7mb / 80.7mb)\nFAIL src/test.ts'
    result = strip_jest_noise(log)
    assert "Downloading MongoDB" not in result
    assert "FAIL src/test.ts" in result


def test_strip_jest_noise_strips_ansi_codes():
    log = "\x1b[31mFAIL\x1b[0m src/test.ts\n  \x1b[31m✕\x1b[0m should work"
    result = strip_jest_noise(log)
    assert "\x1b[" not in result
    assert "FAIL" in result


def test_strip_jest_noise_empty_input():
    assert strip_jest_noise("") == ""


def test_strip_jest_noise_removes_console_blocks():
    log = (
        "  console.error\n"
        "    Error: Apollo handler failed\n"
        "        at Object.<anonymous> (node_modules/jest/build/index.js:100)\n"
        "\n"
        "      88 | if (e instanceof Error) {\n"
        "    > 90 |       console.error(e);\n"
        "\n"
        "  console.warn\n"
        "    AccessDeniedException: not authorized\n"
        "\n"
        "FAIL src/test.ts\n"
        "  ✕ should work\n"
        "error Command failed"
    )
    result = strip_jest_noise(log)
    assert "console.error" not in result
    assert "console.warn" not in result
    assert "Apollo handler" not in result
    assert "AccessDeniedException" not in result
    assert "FAIL src/test.ts" in result
    assert "should work" in result


def test_strip_jest_noise_removes_coverage_table():
    # Real 31K Jest output from foxcom-forms PR#1146 (2026-04-10) with 221-line coverage table.
    # Expected output manually constructed by keeping lines 1-2 + 224-243 (non-table lines).
    fixture_path = os.path.join(FIXTURES_DIR, "foxcom_forms_pr1146_jest_output.txt")
    expected_path = os.path.join(
        FIXTURES_DIR, "foxcom_forms_pr1146_jest_output_expected.txt"
    )

    with open(fixture_path, encoding="utf-8") as f:
        raw = f.read()
    with open(expected_path, encoding="utf-8") as f:
        expected = f.read()

    result = strip_jest_noise(raw)
    assert result.strip() == expected.strip()


def test_strip_jest_noise_real_fixture():
    fixture_path = os.path.join(FIXTURES_DIR, "raw_jest_subprocess_output.txt")
    expected_path = os.path.join(
        FIXTURES_DIR, "raw_jest_subprocess_output_expected.txt"
    )

    with open(fixture_path, encoding="utf-8") as f:
        raw = f.read()
    with open(expected_path, encoding="utf-8") as f:
        expected = f.read()

    result = strip_jest_noise(raw)
    assert result.strip() == expected.strip()

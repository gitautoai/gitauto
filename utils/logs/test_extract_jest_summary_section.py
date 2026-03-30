from utils.logs.extract_jest_summary_section import extract_jest_summary_section


def test_empty_input():
    assert extract_jest_summary_section("") == ""


def test_non_jest_output():
    log = "Some random build output\nno jest here"
    assert extract_jest_summary_section(log) == log


def test_extracts_summary_section():
    log = """lots of verbose output here
PASS src/a.test.ts
FAIL src/b.test.ts
more verbose output
Summary of all failing tests
FAIL src/b.test.ts
  ● Test suite failed

    Error: something broke

Test Suites: 1 failed, 1 passed, 2 total"""

    result = extract_jest_summary_section(log)
    assert "Summary of all failing tests" in result
    assert "Error: something broke" in result
    assert "lots of verbose output here" not in result


def test_preserves_header_commands():
    log = """$ jest --coverage
lots of output
Summary of all failing tests
FAIL src/test.ts
  ● broken test

Test Suites: 1 failed"""

    result = extract_jest_summary_section(log)
    assert "$ jest --coverage" in result
    assert "Summary of all failing tests" in result
    assert "lots of output" not in result


def test_preserves_yarn_header():
    log = """yarn run v1.22.19
$ craco test --coverage
verbose output here
Summary of all failing tests
FAIL test/file.test.tsx
  ● Test A

    Error: fail

Test Suites: 1 failed"""

    result = extract_jest_summary_section(log)
    assert "yarn run v1.22.19" in result
    assert "$ craco test --coverage" in result
    assert "verbose output here" not in result
    assert "Summary of all failing tests" in result

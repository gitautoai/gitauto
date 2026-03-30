from pathlib import Path

from utils.logs.dedup_jest_errors import dedup_jest_errors
from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs


def test_dedup_groups_identical_errors():
    log = """Summary of all failing tests
FAIL test/pages/Account/index.test.tsx (26.865 s)
  ● Test A

    TypeError: Cannot read 'state'

      at Account (src/index.tsx:36:63)
      at Object.<anonymous> (test/index.test.tsx:100:7)

  ● Test B

    TypeError: Cannot read 'state'

      at Account (src/index.tsx:36:63)
      at Object.<anonymous> (test/index.test.tsx:200:7)

  ● Test C

    TypeError: Cannot read 'state'

      at Account (src/index.tsx:36:63)
      at Object.<anonymous> (test/index.test.tsx:300:7)

Test Suites: 1 failed, 1 total"""

    result = dedup_jest_errors(log)
    assert "3 tests failed with this same error:" in result
    assert "● Test A" in result
    assert "● Test B" in result
    assert "● Test C" in result
    # Error body should appear only once (from first test)
    assert result.count("TypeError: Cannot read 'state'") == 1


def test_dedup_keeps_different_errors_separate():
    log = """Summary of all failing tests
FAIL test/file.test.tsx
  ● Test A

    TypeError: Cannot read 'state'

  ● Test B

    ReferenceError: x is not defined

Test Suites: 1 failed, 1 total"""

    result = dedup_jest_errors(log)
    assert "TypeError: Cannot read 'state'" in result
    assert "ReferenceError: x is not defined" in result
    assert "tests failed with this same error" not in result


def test_dedup_handles_single_test():
    log = """FAIL test/file.test.tsx
  ● Only test

    Error: something broke

Test Suites: 1 failed, 1 total"""

    result = dedup_jest_errors(log)
    assert "● Only test" in result
    assert "Error: something broke" in result
    assert "tests failed with this same error" not in result


def test_dedup_handles_empty():
    assert dedup_jest_errors("") == ""


def test_dedup_handles_multiple_file_blocks():
    log = """FAIL test/a.test.tsx
  ● Test 1

    Error: same error

  ● Test 2

    Error: same error

FAIL test/b.test.tsx
  ● Test 3

    Error: different error

Test Suites: 2 failed, 2 total"""

    result = dedup_jest_errors(log)
    assert "2 tests failed with this same error:" in result
    assert "FAIL test/b.test.tsx" in result
    assert "Error: different error" in result


def test_dedup_with_real_fixture():
    """Test with real captured CI log from foxden-admin-portal PR #515 (2026-03-27)."""
    fixture_path = (
        Path(__file__).parent / "fixtures" / "foxden_admin_portal_pr515_original.txt"
    )
    original = fixture_path.read_text()

    result = minimize_jest_test_logs(original)

    # 393K original → should be under 10K after minimization
    assert len(result) < 10_000, f"Minimized log too large: {len(result):,} chars"
    # 39 identical Account errors should be deduped
    assert "39 tests failed with this same error:" in result
    # Non-duplicate errors should still appear
    assert "Exceeded timeout of 5000 ms" in result
    # Summary should be preserved
    assert "Test Suites: 3 failed" in result

from utils.logs.extract_failing_test_files import extract_failing_test_files

# Real CI error log snippets from production CloudWatch logs

JEST_CIRCLECI_LOG = """\
[999D[K  console.log
    MongoDB connection pool closed

      at MongoDBConnection.disconnect (node_modules/@foxden/shared-lib/src/mongoDBConnection.ts:135:17)
          at async Promise.allSettled (index 0)

FAIL integration testing/services/processPreSetupRenewals.test.ts (8.086 s)
  processPreSetupRenewals test
    All payments succeed without errors
      ✓ Should auto-pay a valid pre-setup quote. (371 ms)
      ✗ Should not call createPaymentIntentForAutoPay (40 ms)
PASS testing/models/mongodb/ApplicationStatus.test.ts
FAIL testing/services/processPreSetupRenewals.test.ts (8.086 s)
"""

JEST_MONOREPO_LOG = """\
Test Suites: 16 failed, 53 passed, 69 total
FAIL core src/verbs/util/__tests__/expressions.spec.ts
FAIL core src/resources/DataPackage/__tests__/ResourceManager.spec.ts
FAIL core src/verbs/__tests__/convert.spec.ts
PASS core src/verbs/__tests__/aggregate.spec.ts
"""

VITEST_ANSI_LOG = """\
\x1b[31m\x1b[1m\x1b[7m FAIL \x1b[27m\x1b[22m\x1b[39m src/features/auth/tests/ProtectedRoute.test.tsx\x1b[2m [ src/features/auth/tests/ProtectedRoute.test.tsx ]\x1b[22m
\x1b[31m\x1b[1m\x1b[7m FAIL \x1b[27m\x1b[22m\x1b[39m src/features/auth/tests/LoginPage.test.tsx\x1b[2m > \x1b[22mLoginPage\x1b[2m > \x1b[22mrenders the Sign In button
"""

PYTEST_GITHUB_ACTIONS_LOG = """\
=========================== short test summary info ============================
FAILED tests/test_logic_unit.py::test_calculate_discounted_total_rules[100.0-5-False-90.0] - assert 100.0 == 90.0
 +  where 100.0 = calculate_discounted_total(100.0, 5, False)
FAILED tests/test_logic_unit.py::test_average_score_multiple_values - assert 190.0 == 95.0
 +  where 190.0 = average_score([90, 100])
FAILED tests/test_logic_unit.py::test_is_leap_year_cases[1900-False] - assert True is False
 +  where True = is_leap_year(1900)
FAILED tests/test_logic_unit.py::test_normalize_username_trims_and_lowercases - AssertionError: assert '  alice  ' == 'alice'
FAILED tests/test_logic_unit.py::test_normalize_username_rejects_too_short_after_normalization - Failed: DID NOT RAISE <class 'ValueError'>
5 failed, 17 passed in 0.05s
##[error]Process completed with exit code 1.
"""

PHPUNIT_GITHUB_ACTIONS_LOG = """\
.......................................................       5301 / 5301 (100%)
2026-02-27T00:44:20.3197520Z\x20
Time: 06:39.169, Memory: 475.01 MB
2026-02-27T00:44:20.3198785Z\x20
There was 1 failure:
2026-02-27T00:44:20.3199118Z\x20
1) Tests\\Helpers\\FilesystemTest::testFputcsvFqmConvertsEncodingToShiftJis
Failed asserting that two strings are identical.
--- Expected
+++ Actual
2026-02-27T00:44:20.3203358Z\x20
/home/kf/app/tests/php/unit/core/app/Helpers/filesystemTest.php:84
2026-02-27T00:44:20.3204110Z\x20
FAILURES!
Tests: 5301, Assertions: 14922, Failures: 1, Skipped: 28.
##[error]Process completed with exit code 1.
"""


def test_jest_circleci_real_log():
    result = extract_failing_test_files(JEST_CIRCLECI_LOG)
    assert result == {"testing/services/processPreSetupRenewals.test.ts"}


def test_jest_monorepo_real_log():
    result = extract_failing_test_files(JEST_MONOREPO_LOG)
    assert result == {
        "src/verbs/util/__tests__/expressions.spec.ts",
        "src/resources/DataPackage/__tests__/ResourceManager.spec.ts",
        "src/verbs/__tests__/convert.spec.ts",
    }


def test_vitest_ansi_real_log():
    result = extract_failing_test_files(VITEST_ANSI_LOG)
    assert result == {
        "src/features/auth/tests/ProtectedRoute.test.tsx",
        "src/features/auth/tests/LoginPage.test.tsx",
    }


def test_pytest_github_actions_real_log():
    result = extract_failing_test_files(PYTEST_GITHUB_ACTIONS_LOG)
    assert result == {"tests/test_logic_unit.py"}


def test_phpunit_github_actions_real_log():
    result = extract_failing_test_files(PHPUNIT_GITHUB_ACTIONS_LOG)
    assert result == {"/home/kf/app/tests/php/unit/core/app/Helpers/filesystemTest.php"}


def test_empty_log():
    assert extract_failing_test_files("") == set()


def test_passing_only_log():
    log = "PASS src/a.test.ts\nPASS src/b.test.ts\nAll tests passed"
    assert extract_failing_test_files(log) == set()


def test_mixed_frameworks():
    log = JEST_CIRCLECI_LOG + "\n" + PYTEST_GITHUB_ACTIONS_LOG
    result = extract_failing_test_files(log)
    assert "testing/services/processPreSetupRenewals.test.ts" in result
    assert "tests/test_logic_unit.py" in result

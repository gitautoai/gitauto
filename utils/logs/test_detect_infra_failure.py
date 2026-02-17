# Standard imports
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from utils.logs.detect_infra_failure import detect_infra_failure

# Real CI log from SpiderPlus PR 13615 (segfault during PHPUnit)
SEGFAULT_LOG_PATH = Path("payloads/github/check_suite/segfault_phpunit_log.txt")

NORMAL_TEST_FAILURE_LOG = """\
PHPUnit 9.6.27 by Sebastian Bergmann and contributors.

..........F..F....

FAILURES!
Tests: 18, Assertions: 25, Failures: 2

1) SomeTest::testExample
Failed asserting that 1 is identical to '1'.
"""


def test_detect_infra_failure_real_segfault_log():
    real_log = SEGFAULT_LOG_PATH.read_text()
    result = detect_infra_failure(real_log)
    assert result == "Segmentation fault"


@pytest.mark.parametrize(
    "error_log, expected",
    [
        (NORMAL_TEST_FAILURE_LOG, None),
        ("", None),
    ],
    ids=["normal_test_failure", "empty_log"],
)
def test_detect_infra_failure_no_match(error_log, expected):
    result = detect_infra_failure(error_log)
    assert result == expected

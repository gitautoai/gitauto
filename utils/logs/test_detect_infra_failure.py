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
        # Package registry failures
        (
            'error An unexpected error occurred: "https://registry.yarnpkg.com/...: '
            'Request failed "502 Bad Gateway""\n',
            'Request failed "502 Bad Gateway"',
        ),
        (
            'Request failed "503 Service Unavailable"',
            'Request failed "503 Service Unavailable"',
        ),
        (
            'Request failed "429 Too Many Requests"',
            'Request failed "429 Too Many Requests"',
        ),
        # Network errors
        ("npm ERR! code ETIMEDOUT\nnpm ERR! errno ETIMEDOUT", "ETIMEDOUT"),
        ("npm ERR! code ECONNRESET", "ECONNRESET"),
        ("npm ERR! code ECONNREFUSED", "ECONNREFUSED"),
        ("getaddrinfo EAI_AGAIN registry.npmjs.org", "EAI_AGAIN"),
        # CI timeouts
        (
            "Too long with no output (exceeded 10m0s): context deadline exceeded",
            "Too long with no output",
        ),
        ("context deadline exceeded", "context deadline exceeded"),
        # OOM
        (
            "FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed - JavaScript heap out of memory",
            "out of memory",
        ),
        ("bash: line 1: 12345 Killed (exit code 137)", "exit code 137"),
        ("Cannot allocate memory (errno: ENOMEM)", "ENOMEM"),
        # MongoMemoryServer binary crash
        (
            "Starting the MongoMemoryServer Instance failed, enable debug log for more information. Error:\n"
            ' UnexpectedCloseError: Instance closed unexpectedly with code "null" and signal "SIGABRT"',
            "MongoMemoryServer Instance failed",
        ),
        (
            'Instance closed unexpectedly with code "null" and signal "SIGABRT"\n'
            "    at ChildProcess.emit (node:events:519:28)",
            'signal "SIGABRT"',
        ),
    ],
    ids=[
        "yarn_502",
        "503_service_unavailable",
        "429_too_many_requests",
        "etimedout",
        "econnreset",
        "econnrefused",
        "eai_again",
        "ci_timeout",
        "context_deadline",
        "oom_js_heap",
        "exit_code_137",
        "enomem",
        "mongoms_instance_failed",
        "sigabrt",
    ],
)
def test_detect_infra_failure_matches(error_log, expected):
    result = detect_infra_failure(error_log)
    assert result == expected


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

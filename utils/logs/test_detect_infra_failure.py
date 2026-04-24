# Standard imports
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from utils.logs.detect_infra_failure import detect_infra_failure

# Real CI log from SpiderPlus PR 13615 (segfault during PHPUnit)
SEGFAULT_LOG_PATH = Path("payloads/github/check_suite/segfault_phpunit_log.txt")

# Real CircleCI `test` job log from Foxquilt/foxden-rating-quoting-backend PR 714.
# App-level console.warn at the top contains "AccessDeniedException" (SSM fetch fell back to defaults — harmless).
# Jest ran to completion and reported `Tests: 2 failed, 35 skipped, 4500 passed` from real assertion bugs in the PR.
# detect_infra_failure used to match "AccessDeniedException" and send the PR down the infra-retry branch, burning 3 empty-commit retries without ever invoking the LLM fix path.
# Must now classify as None (code bug).
PR714_FOXDEN_RATING_QUOTING_LOG_PATH = Path(
    "utils/logs/fixtures/foxden_rating_quoting_pr714_circleci_log.txt"
)
PR1157_FOXCOM_FORMS_CODECOV_CHECKSUM_LOG_PATH = Path(
    "utils/logs/fixtures/foxcom_forms_pr1157_codecov_checksum_circleci_log.txt"
)
PR1158_FOXCOM_FORMS_CODECOV_BAD_SIGNATURE_LOG_PATH = Path(
    "utils/logs/fixtures/foxcom_forms_pr1158_codecov_bad_signature_circleci_log.txt"
)

NORMAL_TEST_FAILURE_LOG = """\
PHPUnit 9.6.27 by Sebastian Bergmann and contributors.

..........F..F....

FAILURES!
Tests: 18, Assertions: 25, Failures: 2

1) SomeTest::testExample
Failed asserting that 1 is identical to '1'.
"""

TERRAFORM_BUCKET_REGION_ERROR_LOG = """\
CircleCI Build Log: terraform init

Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
Error refreshing state: BucketRegionError: incorrect region, the bucket is not in 'us-west-1' region at endpoint '', bucket is in 'eu-west-3' region
status code: 301
"""


def test_detect_infra_failure_real_segfault_log():
    real_log = SEGFAULT_LOG_PATH.read_text(encoding="utf-8")
    result = detect_infra_failure(real_log)
    assert result == "Segmentation fault"


@pytest.mark.parametrize(
    "error_log, expected",
    [
        # Package registry failures
        (
            TERRAFORM_BUCKET_REGION_ERROR_LOG,
            "BucketRegionError",
        ),
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
        # AWS IAM permission errors
        (
            "AccessDeniedException: User: arn:aws:sts::948023073771:assumed-role/pr-agent-prod-role/pr-agent-prod "
            "is not authorized to perform: secretsmanager:GetSecretValue on resource: dev/foxden-billing "
            "because no identity-based policy allows the secretsmanager:GetSecretValue action",
            "AccessDeniedException",
        ),
        (
            "User: arn:aws:sts::123:assumed-role/role/func is not authorized to perform: ssm:GetParameter "
            "because no identity-based policy allows the ssm:GetParameter action",
            "no identity-based policy allows",
        ),
    ],
    ids=[
        "terraform_bucket_region_error",
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
        "aws_access_denied",
        "aws_iam_policy_denied",
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


def test_strip_jest_noise_removes_app_level_access_denied_warn():
    # Real PR 714 CircleCI log: app-level console.warn at the top prints "AccessDeniedException" from an SSM fetch that fell back to a default.
    # strip_jest_noise removes that console block inside detect_infra_failure, so the spurious match no longer routes the PR to the infra-retry path.
    # Jest still ran and reported real assertion failures further down; classifier must return None so the LLM fix path handles them.
    real_log = PR714_FOXDEN_RATING_QUOTING_LOG_PATH.read_text(encoding="utf-8")
    assert detect_infra_failure(real_log) is None


def test_detect_infra_failure_real_codecov_checksum_mismatch_log():
    real_log = PR1157_FOXCOM_FORMS_CODECOV_CHECKSUM_LOG_PATH.read_text(
        encoding="utf-8"
    )
    assert detect_infra_failure(real_log) == "Validate Codecov Uploader"


def test_detect_infra_failure_real_codecov_bad_signature_log():
    real_log = PR1158_FOXCOM_FORMS_CODECOV_BAD_SIGNATURE_LOG_PATH.read_text(
        encoding="utf-8"
    )
    assert detect_infra_failure(real_log) == "Validate Codecov Uploader"

from typing import TypedDict

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.logs.strip_jest_noise import strip_jest_noise


class InfraFailureMatch(TypedDict):
    pattern: str
    should_retry: bool


# Patterns for transient infrastructure failures (not code bugs).
# Add more as we encounter them.
INFRA_FAILURE_PATTERNS: list[InfraFailureMatch] = [
    # Codecov uploader validation failures. These resolve when vendor-side signing artifacts settle, not by our empty commits.
    {"pattern": "Validate Codecov Uploader", "should_retry": False},
    {"pattern": "computed checksum did NOT match", "should_retry": False},
    {"pattern": 'BAD signature from "Codecov Uploader', "should_retry": False},
    # Segfaults
    {"pattern": "Segmentation fault", "should_retry": True},
    {"pattern": "exit code 139", "should_retry": True},
    # Terraform / AWS backend misconfiguration
    {"pattern": "BucketRegionError", "should_retry": True},
    {"pattern": "incorrect region, the bucket is not in", "should_retry": True},
    # Package registry failures
    {"pattern": 'Request failed "502 Bad Gateway"', "should_retry": True},
    {"pattern": 'Request failed "503 Service Unavailable"', "should_retry": True},
    {"pattern": 'Request failed "429 Too Many Requests"', "should_retry": True},
    {"pattern": "ETIMEDOUT", "should_retry": True},
    {"pattern": "ECONNRESET", "should_retry": True},
    {"pattern": "ECONNREFUSED", "should_retry": True},
    {"pattern": "EAI_AGAIN", "should_retry": True},
    # CI timeouts
    {"pattern": "Too long with no output", "should_retry": True},
    {"pattern": "context deadline exceeded", "should_retry": True},
    # OOM
    {"pattern": "out of memory", "should_retry": True},
    {"pattern": "exit code 137", "should_retry": True},
    {"pattern": "ENOMEM", "should_retry": True},
    # MongoMemoryServer binary crash (version/distro mismatch with cached S3 binary)
    {"pattern": "MongoMemoryServer Instance failed", "should_retry": True},
    {"pattern": 'signal "SIGABRT"', "should_retry": True},
    # AWS IAM permission errors (Lambda role lacks access to SSM/SecretsManager/etc.)
    {"pattern": "AccessDeniedException", "should_retry": True},
    {"pattern": "no identity-based policy allows", "should_retry": True},
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def detect_infra_failure(error_log: str):
    # Strip console.warn/log blocks and AWS SSM-fallback warnings before scanning so app-level noise (e.g. "AccessDeniedException" from a console.warn that fell back to a default) can't false-positive this classifier.
    error_log = strip_jest_noise(error_log)
    lower_log = error_log.lower()
    for infra_failure in INFRA_FAILURE_PATTERNS:
        if infra_failure["pattern"].lower() in lower_log:
            logger.info(
                "Infrastructure failure detected: pattern='%s' should_retry=%s",
                infra_failure["pattern"],
                infra_failure["should_retry"],
            )
            return infra_failure

    logger.info("No infrastructure failure pattern matched")
    return None

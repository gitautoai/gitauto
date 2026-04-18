# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Patterns for transient infrastructure failures (not code bugs). Add more as we encounter them.
INFRA_FAILURE_PATTERNS = [
    # Segfaults
    "Segmentation fault",
    "exit code 139",
    # Package registry failures
    'Request failed "502 Bad Gateway"',
    'Request failed "503 Service Unavailable"',
    'Request failed "429 Too Many Requests"',
    "ETIMEDOUT",
    "ECONNRESET",
    "ECONNREFUSED",
    "EAI_AGAIN",
    # CI timeouts
    "Too long with no output",
    "context deadline exceeded",
    # OOM
    "out of memory",
    "exit code 137",
    "ENOMEM",
    # MongoMemoryServer binary crash (version/distro mismatch with cached S3 binary)
    "MongoMemoryServer Instance failed",
    'signal "SIGABRT"',
    # AWS IAM permission errors (Lambda role lacks access to SSM/SecretsManager/etc.)
    "AccessDeniedException",
    "no identity-based policy allows",
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def detect_infra_failure(error_log: str):
    lower_log = error_log.lower()
    for pattern in INFRA_FAILURE_PATTERNS:
        if pattern.lower() in lower_log:
            logger.info("Infrastructure failure detected: '%s'", pattern)
            return pattern

    return None

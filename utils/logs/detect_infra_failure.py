# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Only patterns we've actually observed in real CI logs. Add more as we encounter them.
INFRA_FAILURE_PATTERNS = [
    "Segmentation fault",
    "exit code 139",
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def detect_infra_failure(error_log: str):
    lower_log = error_log.lower()
    for pattern in INFRA_FAILURE_PATTERNS:
        if pattern.lower() in lower_log:
            logger.info("Infrastructure failure detected: '%s'", pattern)
            return pattern

    return None

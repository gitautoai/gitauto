from utils.error.is_server_error import is_server_error
from utils.logging.logging_config import logger

# Marker strings that indicate a transient GitHub-side failure surfaced through
# non-HTTPError exceptions (e.g. ValueError from run_subprocess wrapping `git
# push` stderr). Matched case-sensitive to avoid false positives on user text.
TRANSIENT_MARKERS = (
    "remote: Internal Server Error",
    "502 Bad Gateway",
    "503 Service Unavailable",
    "504 Gateway Timeout",
    "HTTP 500",
    "HTTP 502",
    "HTTP 503",
    "HTTP 504",
)


def is_transient_error(err: Exception):
    """Return True when the exception represents a transient upstream failure
    worth retrying. Covers both HTTP-shaped errors (via is_server_error) and
    string-reported errors from subprocesses that the agent's retry path can
    safely try again."""
    if is_server_error(err):
        logger.info("is_transient_error: matched via is_server_error")
        return True

    # Google GenAI returns 499 CANCELLED when its own backend closes the stream, observed during free-tier overload windows (sibling symptom of 429 RESOURCE_EXHAUSTED, but without a Retry-After hint). Retry like any 5xx via the caller's linear backoff.
    if getattr(err, "code", None) == 499:
        logger.info("is_transient_error: matched via code=499 CANCELLED")
        return True

    err_text = str(err)
    matched = any(marker in err_text for marker in TRANSIENT_MARKERS)
    logger.info("is_transient_error: marker match=%s", matched)
    return matched

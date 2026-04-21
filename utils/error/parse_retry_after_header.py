from utils.logging.logging_config import logger


def parse_retry_after_header(headers):
    """Parse an HTTP Retry-After header value (RFC 7231) and return it as float seconds, or None when absent/unparseable.

    Used by GitHub's secondary rate limit, Anthropic's RateLimitError, and any generic 429 response that sets Retry-After.
    The spec allows either a non-negative integer (seconds) or an HTTP-date; in practice SDKs almost always return seconds.
    We accept numeric values only — the date-form is uncommon and handling it would mean parsing three different datetime conventions for a code path we have never seen in production.
    """
    if not headers:
        logger.info("parse_retry_after_header: no headers object on response")
        return None

    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        logger.info("parse_retry_after_header: no Retry-After header present")
        return None

    try:
        delay = float(raw)
    except (TypeError, ValueError):
        logger.info(
            "parse_retry_after_header: Retry-After=%r is not a number; ignoring (date-form unsupported)",
            raw,
        )
        return None

    logger.info("parse_retry_after_header: parsed %.2fs from Retry-After", delay)
    return delay

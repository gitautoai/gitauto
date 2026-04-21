import time

from utils.error.parse_retry_after_header import parse_retry_after_header
from utils.logging.logging_config import logger


def parse_github_rate_limit_headers(response):
    """Parse GitHub's rate-limit headers into a retry delay in seconds, or None when the response is not a github rate limit.

    GitHub signals a primary rate limit by `X-RateLimit-Remaining: 0`, with `X-RateLimit-Reset` giving the unix timestamp when the quota refills.
    A secondary (abuse) rate limit uses the standard Retry-After header instead.
    Both shapes can coexist. If this function sees a non-zero remaining, it falls back to Retry-After (secondary limit case).
    We add a 5s buffer on top of the reset timestamp to guard against small clock skew between the Lambda and GitHub's servers — without it, a retry that fires exactly at reset time occasionally still hits the 403.
    """
    headers = getattr(response, "headers", None)
    if not headers:
        logger.info("parse_github_rate_limit_headers: github response has no headers")
        return None

    remaining_raw = headers.get("X-RateLimit-Remaining")
    if remaining_raw is None:
        logger.info(
            "parse_github_rate_limit_headers: no X-RateLimit-Remaining header; not a github rate limit"
        )
        return None

    try:
        remaining = int(remaining_raw)
    except (TypeError, ValueError):
        logger.info(
            "parse_github_rate_limit_headers: X-RateLimit-Remaining=%r unparseable; ignoring",
            remaining_raw,
        )
        return None

    if remaining > 0:
        logger.info(
            "parse_github_rate_limit_headers: X-RateLimit-Remaining=%d > 0; trying Retry-After for secondary limit",
            remaining,
        )
        return parse_retry_after_header(headers)

    reset_raw = headers.get("X-RateLimit-Reset")
    if reset_raw is None:
        logger.info(
            "parse_github_rate_limit_headers: primary rate limit but no X-RateLimit-Reset header; falling back to Retry-After"
        )
        return parse_retry_after_header(headers)

    try:
        reset_ts = int(reset_raw)
    except (TypeError, ValueError):
        logger.info(
            "parse_github_rate_limit_headers: X-RateLimit-Reset=%r unparseable; ignoring",
            reset_raw,
        )
        return None

    delay = float(reset_ts - int(time.time()))
    if delay > 0:
        logger.info(
            "parse_github_rate_limit_headers: primary rate limit resets in %.2fs; adding 5s buffer",
            delay,
        )
        delay += 5.0
    else:
        logger.info(
            "parse_github_rate_limit_headers: rate-limit reset already past; using 1s minimum"
        )
        delay = 1.0
    limit = headers.get("X-RateLimit-Limit", "?")
    used = headers.get("X-RateLimit-Used", "?")
    logger.info(
        "parse_github_rate_limit_headers: github primary limit exhausted (limit=%s used=%s); honoring %.2fs",
        limit,
        used,
        delay,
    )
    return delay

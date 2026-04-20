import time
from typing import Any, Callable

import requests
import sentry_sdk

from utils.logging.logging_config import logger


def handle_github_rate_limit(
    err: requests.HTTPError,
    func_name: str,
    reason: str,
    text: str,
    raise_on_error: bool,
    retry_callback: Callable[[], Any],
):
    """Handle GitHub's 403/429 responses for primary and secondary rate limits.

    Returns (retry_result, True) when a retry was performed; returns None when
    the caller should fall through to generic Sentry-capture-and-return
    behaviour (non-rate-limit 403/429, or raise_on_error already raised)."""
    assert err.response is not None
    logger.error("err.response.headers: %s", err.response.headers)
    limit = int(err.response.headers["X-RateLimit-Limit"])
    remaining = int(err.response.headers["X-RateLimit-Remaining"])
    used = int(err.response.headers["X-RateLimit-Used"])

    if remaining == 0:
        logger.info("%s GitHub primary rate limit exhausted", func_name)
        reset_ts = int(err.response.headers.get("X-RateLimit-Reset", 0))
        current_ts = int(time.time())
        wait_time = reset_ts - current_ts

        if wait_time <= 0:
            logger.info("%s rate-limit reset already past, waiting 1s", func_name)
            wait_time = 1
        else:
            logger.info("%s waiting %ds for rate-limit reset", func_name, wait_time)
            wait_time = wait_time + 5

        err_msg = f"{func_name} encountered a GitHubPrimaryRateLimitError: {err}. Retrying after {wait_time} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
        logger.error(err_msg)
        time.sleep(wait_time)
        logger.info("%s invoking primary-rate-limit retry", func_name)
        return retry_callback(), True

    if "exceeded a secondary rate limit" in err.response.text.lower():
        logger.info("%s GitHub secondary rate limit hit", func_name)
        retry_after = int(err.response.headers.get("Retry-After", 60))
        err_msg = f"{func_name} encountered a GitHubSecondaryRateLimitError: {err}. Retrying after {retry_after} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
        logger.error(err_msg)
        time.sleep(retry_after)
        logger.info("%s invoking secondary-rate-limit retry", func_name)
        return retry_callback(), True

    err_msg = f"{func_name} encountered an HTTPError: {err}. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
    sentry_sdk.capture_exception(err)
    logger.error(err_msg)
    if raise_on_error:
        logger.error("%s re-raising 403/429 HTTPError", func_name)
        raise err

    logger.info("%s 403/429 non-rate-limit, falling through to default", func_name)
    return None

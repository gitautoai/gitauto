import requests

from utils.error.parse_github_rate_limit_headers import (
    parse_github_rate_limit_headers,
)
from utils.error.parse_google_retry_in_message import parse_google_retry_in_message
from utils.error.parse_retry_after_header import parse_retry_after_header
from utils.logging.logging_config import logger


def get_rate_limit_retry_after(err: Exception):
    """Return the SDK's suggested retry delay in seconds when the error is a rate limit, None otherwise.

    Sentry AGENT-3K5/3K6/3K7/3K8/36M/36Q (Gemini free-tier 429 cascading through chat_with_google → chat_with_model → chat_with_agent → handle_webhook_event): Gemini embeds "Please retry in N.NNNs" in the error message body.
    GitHub uses X-RateLimit-Reset/Retry-After headers. Anthropic uses retry-after and anthropic-ratelimit-* headers.
    Rather than duplicate sleep+retry logic per SDK, return a single delay that handle_exceptions can honor uniformly.
    No upper bound is applied: honor whatever the server suggested. Lambda-timeout protection already exists at the handler layer via should_bail().
    """
    # requests.HTTPError (GitHub, generic 429 APIs)
    if isinstance(err, requests.HTTPError):
        logger.info("get_rate_limit_retry_after: dispatching requests.HTTPError branch")
        response = getattr(err, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code not in (403, 429):
            logger.info(
                "get_rate_limit_retry_after: requests.HTTPError status=%s not in {403,429}",
                status_code,
            )
            return None
        headers = getattr(response, "headers", None) if response is not None else None
        if headers and "X-RateLimit-Remaining" in headers:
            logger.info(
                "get_rate_limit_retry_after: detected github rate-limit headers"
            )
            return parse_github_rate_limit_headers(response)
        logger.info(
            "get_rate_limit_retry_after: no github-specific headers; using Retry-After path"
        )
        return parse_retry_after_header(headers)

    # Anthropic RateLimitError / APIStatusError with status_code=429
    status_code = getattr(err, "status_code", None)
    if isinstance(status_code, int) and status_code == 429:
        logger.info(
            "get_rate_limit_retry_after: dispatching anthropic status_code=429 branch"
        )
        response = getattr(err, "response", None)
        headers = getattr(response, "headers", None) if response is not None else None
        logger.info(
            "get_rate_limit_retry_after: delegating anthropic delay extraction to parse_retry_after_header"
        )
        return parse_retry_after_header(headers)

    # Google GenAI ClientError with code=429 (message body carries the hint)
    code = getattr(err, "code", None)
    if code == 429:
        logger.info("get_rate_limit_retry_after: dispatching google code=429 branch")
        return parse_google_retry_in_message(err)

    logger.info(
        "get_rate_limit_retry_after: %s is not a recognized rate-limit error",
        type(err).__name__,
    )
    return None

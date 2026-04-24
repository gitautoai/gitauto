import json
from typing import Any, Callable

import requests
import sentry_sdk

from utils.error.is_server_error import is_server_error
from utils.logging.logging_config import logger


def handle_http_error(
    err: requests.HTTPError,
    func_name: str,
    log_args: list,
    log_kwargs: dict,
    api_type: str,
    raise_on_error: bool,
    error_return: Any,
    retry_callback: Callable[[], Any],
):
    # Rate-limit retry (github primary/secondary, generic Retry-After) is handled at the outer handle_exceptions level via get_rate_limit_retry_after. By the time we get here, a rate-limited HTTPError means the retry budget was already exhausted — treat it like any other HTTPError.
    _ = retry_callback  # kept in signature for backward-compat with handle_exceptions
    if err.response is None:
        if raise_on_error:
            logger.error("%s HTTPError with no response; re-raising", func_name)
            raise err
        logger.info("%s HTTPError with no response; returning default", func_name)
        return error_return, False

    status_code: int = err.response.status_code

    if is_server_error(err):
        if raise_on_error:
            logger.error(
                "%s server error %s; re-raising (not reported to Sentry)",
                func_name,
                status_code,
            )
            raise err

        logger.warning(
            "%s server error %s; returning default (not reported to Sentry)",
            func_name,
            status_code,
        )
        return error_return, False

    reason: str | Any = (
        str(err.response.reason) if err.response.reason is not None else "Unknown"
    )
    text: str | Any = (
        str(err.response.text) if err.response.text is not None else "Unknown"
    )
    logger.error("reason: %s, text: %s, status_code: %s", reason, text, status_code)

    if api_type == "web_search" and status_code == 429:
        logger.error(
            "%s web_search hit 429: Web Search Rate Limit; headers=%s; raising",
            func_name,
            err.response.headers,
        )
        raise err

    logger.info("%s reporting HTTPError to Sentry", func_name)
    err_msg = f"{func_name} encountered an HTTPError: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}\n\nReason: {reason}\n\nText: {text}"
    sentry_sdk.capture_exception(err)
    logger.error(err_msg)

    if raise_on_error:
        logger.error("%s HTTPError path re-raising", func_name)
        raise err

    logger.info("%s HTTPError path returning default", func_name)
    return error_return, False

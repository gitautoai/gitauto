import json
from typing import Any, Callable

import requests
import sentry_sdk

from utils.error.handle_github_rate_limit import handle_github_rate_limit
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
    if err.response is None:
        logger.info("%s HTTPError has no response object", func_name)
        if raise_on_error:
            logger.error("%s HTTPError with no response, re-raising", func_name)
            raise err

        logger.info("%s HTTPError with no response, returning default", func_name)
        return error_return, False

    status_code: int = err.response.status_code

    if is_server_error(err):
        logger.warning(
            "%s received server error %s, not reporting to Sentry",
            func_name,
            status_code,
        )
        if raise_on_error:
            logger.error("%s re-raising server error %s", func_name, status_code)
            raise err

        logger.info("%s returning default for server error %s", func_name, status_code)
        return error_return, False

    reason: str | Any = (
        str(err.response.reason) if err.response.reason is not None else "Unknown"
    )
    text: str | Any = (
        str(err.response.text) if err.response.text is not None else "Unknown"
    )
    logger.error("reason: %s, text: %s, status_code: %s", reason, text, status_code)

    if api_type == "github" and status_code in {403, 429}:
        logger.info("%s dispatching to github rate-limit handler", func_name)
        retry_result = handle_github_rate_limit(
            err, func_name, reason, text, raise_on_error, retry_callback
        )
        if retry_result is not None:
            logger.info("%s github 403/429 returned retry result", func_name)
            return retry_result

    elif api_type == "web_search" and status_code == 429:
        logger.info("%s web_search hit 429, raising", func_name)
        err_msg = f"Web Search Rate Limit in {func_name}()"
        logger.error(err_msg)
        logger.error("err.response.headers: %s", err.response.headers)
        raise err

    else:
        logger.info("%s reporting HTTPError to Sentry", func_name)
        err_msg = f"{func_name} encountered an HTTPError: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}\n\nReason: {reason}\n\nText: {text}"
        sentry_sdk.capture_exception(err)
        logger.error(err_msg)

    if raise_on_error:
        logger.error("%s HTTPError path re-raising", func_name)
        raise err

    logger.info("%s HTTPError path returning default", func_name)
    return error_return, False

import json
from typing import Any

import sentry_sdk

from utils.logging.logging_config import logger


def handle_json_error(
    err: json.JSONDecodeError,
    func_name: str,
    log_args: list,
    log_kwargs: dict,
    raise_on_error: bool,
    error_return: Any,
):
    raw_response = err.doc if hasattr(err, "doc") else "Raw response not available"
    err_msg = f"{func_name} encountered a JSONDecodeError: {err}\n\nRaw response: {raw_response}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}"
    sentry_sdk.capture_exception(err)
    logger.error(err_msg)
    if raise_on_error:
        logger.error("%s JSONDecodeError re-raising", func_name)
        raise err

    logger.info("%s JSONDecodeError returning default", func_name)
    return error_return

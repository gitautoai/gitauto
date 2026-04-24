import json
from typing import Any

import sentry_sdk

from utils.error.is_billing_error import is_billing_error
from utils.error.is_server_error import is_server_error
from utils.logging.logging_config import logger


def handle_generic_error(
    err: Exception,
    func_name: str,
    log_args: list,
    log_kwargs: dict,
    raise_on_error: bool,
    error_return: Any,
):
    err_msg = f"{func_name} encountered an {type(err).__name__}: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}"

    if is_server_error(err):
        logger.warning(
            "%s server error (not reported to Sentry):\n%s", func_name, err_msg
        )
    elif is_billing_error(err):
        logger.warning(
            "%s billing error (not reported to Sentry):\n%s", func_name, err_msg
        )
    else:
        sentry_sdk.capture_exception(err)
        logger.error("%s generic error reported to Sentry:\n%s", func_name, err_msg)

    if raise_on_error:
        logger.error("%s generic error re-raising", func_name)
        raise err

    logger.info("%s generic error returning default", func_name)
    return error_return

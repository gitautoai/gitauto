# flake8: noqa: E704 - overload stubs use `...` on same line as `def`
# pylint: disable=broad-exception-caught

# Standard imports
import asyncio
from functools import wraps
import inspect
import json
import time
from typing import Any, Callable, Literal, ParamSpec, TypeVar, cast, overload

# Third party imports
import requests
import sentry_sdk

from utils.logging.logging_config import logger

P = ParamSpec("P")  # Function parameters (args, kwargs)
R = TypeVar("R")  # Return type of decorated function
D = TypeVar("D")  # Default return value type


@overload
def handle_exceptions(
    default_return_value: Any = None,
    raise_on_error: Literal[True] = ...,
    api_type: str = "github",
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


@overload
def handle_exceptions(
    default_return_value: Callable[..., R],
    raise_on_error: Literal[False] = ...,
    api_type: str = "github",
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


@overload
def handle_exceptions(
    default_return_value: None = None,
    raise_on_error: Literal[False] = ...,
    api_type: str = "github",
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


@overload
def handle_exceptions(
    default_return_value: object,
    raise_on_error: Literal[False] = ...,
    api_type: str = "github",
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def _handle_http_error(
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
        if raise_on_error:
            raise err
        return error_return, False

    status_code: int = err.response.status_code

    if status_code >= 500:
        logger.warning("%s received server error %s, not reporting to Sentry", func_name, status_code)
        if raise_on_error:
            raise err
        return error_return, False

    reason: str | Any = (
        str(err.response.reason) if err.response.reason is not None else "Unknown"
    )
    text: str | Any = (
        str(err.response.text) if err.response.text is not None else "Unknown"
    )
    logger.error("reason: %s, text: %s, status_code: %s", reason, text, status_code)

    if api_type == "github" and status_code in {403, 429}:
        logger.error("err.response.headers: %s", err.response.headers)
        limit = int(err.response.headers["X-RateLimit-Limit"])
        remaining = int(err.response.headers["X-RateLimit-Remaining"])
        used = int(err.response.headers["X-RateLimit-Used"])

        if remaining == 0:
            reset_ts = int(err.response.headers.get("X-RateLimit-Reset", 0))
            current_ts = int(time.time())
            wait_time = reset_ts - current_ts
            if wait_time <= 0:
                wait_time = 1
            else:
                wait_time = wait_time + 5
            err_msg = f"{func_name} encountered a GitHubPrimaryRateLimitError: {err}. Retrying after {wait_time} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
            logger.error(err_msg)
            time.sleep(wait_time)
            return retry_callback(), True

        if "exceeded a secondary rate limit" in err.response.text.lower():
            retry_after = int(err.response.headers.get("Retry-After", 60))
            err_msg = f"{func_name} encountered a GitHubSecondaryRateLimitError: {err}. Retrying after {retry_after} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
            logger.error(err_msg)
            time.sleep(retry_after)
            return retry_callback(), True

        err_msg = f"{func_name} encountered an HTTPError: {err}. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
        sentry_sdk.capture_exception(err)
        logger.error(err_msg)
        if raise_on_error:
            raise err

    elif api_type == "google" and status_code == 429:
        err_msg = f"Google Search Rate Limit in {func_name}()"
        logger.error(err_msg)
        logger.error("err.response.headers: %s", err.response.headers)
        raise err

    else:
        err_msg = f"{func_name} encountered an HTTPError: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}\n\nReason: {reason}\n\nText: {text}"
        sentry_sdk.capture_exception(err)
        logger.error(err_msg)

    if raise_on_error:
        raise err
    return error_return, False


def _handle_json_error(
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
        raise err
    return error_return


def _handle_generic_error(
    err: Exception,
    func_name: str,
    log_args: list,
    log_kwargs: dict,
    raise_on_error: bool,
    error_return: Any,
):
    err_msg = f"{func_name} encountered an {type(err).__name__}: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}"
    sentry_sdk.capture_exception(err)
    logger.error(err_msg)
    if raise_on_error:
        raise err
    return error_return


def handle_exceptions(
    default_return_value: Any = None,
    raise_on_error: bool = False,
    api_type: str = "github",
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#checking-the-status-of-your-rate-limit"""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):

            @wraps(wrapped=func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                log_args = list(args)
                log_kwargs = dict(kwargs)

                if callable(default_return_value):
                    error_return = default_return_value(*args, **kwargs)
                else:
                    error_return = default_return_value

                try:
                    return await func(*args, **kwargs)
                except requests.HTTPError as err:
                    result, retried = _handle_http_error(
                        err,
                        func.__name__,
                        log_args,
                        log_kwargs,
                        api_type,
                        raise_on_error,
                        error_return,
                        lambda: async_wrapper(*args, **kwargs),
                    )
                    if retried:
                        return await result
                    return cast(R, result)
                except json.JSONDecodeError as err:
                    return cast(
                        R,
                        _handle_json_error(
                            err,
                            func.__name__,
                            log_args,
                            log_kwargs,
                            raise_on_error,
                            error_return,
                        ),
                    )
                except asyncio.CancelledError:
                    logger.warning("%s was cancelled (CancelledError)", func.__name__)
                    if raise_on_error:
                        raise
                    return cast(R, error_return)
                except Exception as err:
                    return cast(
                        R,
                        _handle_generic_error(
                            err,
                            func.__name__,
                            log_args,
                            log_kwargs,
                            raise_on_error,
                            error_return,
                        ),
                    )

            return cast(Callable[P, R], async_wrapper)

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log_args = list(args)
            log_kwargs = dict(kwargs)

            if callable(default_return_value):
                error_return = default_return_value(*args, **kwargs)
            else:
                error_return = default_return_value

            try:
                return func(*args, **kwargs)
            except requests.HTTPError as err:
                result, retried = _handle_http_error(
                    err,
                    func.__name__,
                    log_args,
                    log_kwargs,
                    api_type,
                    raise_on_error,
                    error_return,
                    lambda: wrapper(*args, **kwargs),
                )
                if retried:
                    return cast(R, result)
                return cast(R, result)
            except json.JSONDecodeError as err:
                return cast(
                    R,
                    _handle_json_error(
                        err,
                        func.__name__,
                        log_args,
                        log_kwargs,
                        raise_on_error,
                        error_return,
                    ),
                )
            except Exception as err:
                return cast(
                    R,
                    _handle_generic_error(
                        err,
                        func.__name__,
                        log_args,
                        log_kwargs,
                        raise_on_error,
                        error_return,
                    ),
                )

        return wrapper

    return decorator

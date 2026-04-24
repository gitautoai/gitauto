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

from utils.error.get_rate_limit_retry_after import get_rate_limit_retry_after
from utils.error.handle_generic_error import handle_generic_error
from utils.error.handle_http_error import handle_http_error
from utils.error.handle_json_error import handle_json_error
from utils.error.is_transient_error import is_transient_error
from utils.logging.logging_config import logger

P = ParamSpec("P")  # Function parameters (args, kwargs)
R = TypeVar("R")  # Return type of decorated function
D = TypeVar("D")  # Default return value type

# Retry policy for transient-error retries. 5xx responses almost always mean the server did not complete the operation, so retry is safe by default. Kept small so non-retryable bugs still surface quickly in Sentry.
TRANSIENT_MAX_ATTEMPTS = 3
TRANSIENT_BACKOFF_SECONDS = 2


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


def handle_exceptions(
    default_return_value: Any = None,
    raise_on_error: bool = False,
    api_type: str = "github",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#checking-the-status-of-your-rate-limit

    Transient upstream failures (GitHub 5xx, remote Internal Server Error from subprocess, etc., per is_transient_error) are retried up to TRANSIENT_MAX_ATTEMPTS times with linear backoff. 5xx responses almost always mean the server did not complete the operation, so retry is safe by default for all decorated functions.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):

            @wraps(wrapped=func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                log_args = list(args)
                log_kwargs = dict(kwargs)
                if callable(default_return_value):
                    logger.info(
                        "%s computing default_return_value callable", func.__name__
                    )
                    error_return = default_return_value(*args, **kwargs)
                else:
                    logger.info("%s using static default_return_value", func.__name__)
                    error_return = default_return_value
                remaining_transient_retries = TRANSIENT_MAX_ATTEMPTS - 1
                attempt = 0
                while True:
                    attempt += 1
                    try:
                        logger.info("%s invoking attempt %d", func.__name__, attempt)
                        return await func(*args, **kwargs)
                    except requests.HTTPError as err:
                        rate_limit_delay = get_rate_limit_retry_after(err)
                        if (
                            rate_limit_delay is not None
                            and remaining_transient_retries > 0
                        ):
                            logger.warning(
                                "%s rate-limited via HTTPError on attempt %d; sleeping %.2fs then retrying",
                                func.__name__,
                                attempt,
                                rate_limit_delay,
                            )
                            remaining_transient_retries -= 1
                            await asyncio.sleep(rate_limit_delay)
                            continue
                        logger.info(
                            "%s HTTPError not rate-limited or retries exhausted; handing off",
                            func.__name__,
                        )
                        result, retried = handle_http_error(
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
                            logger.info(
                                "%s HTTPError awaiting retry result", func.__name__
                            )
                            return await result
                        logger.info("%s HTTPError returning non-retry", func.__name__)
                        return cast(R, result)
                    except json.JSONDecodeError as err:
                        logger.info(
                            "%s hit JSONDecodeError, handing off", func.__name__
                        )
                        return cast(
                            R,
                            handle_json_error(
                                err,
                                func.__name__,
                                log_args,
                                log_kwargs,
                                raise_on_error,
                                error_return,
                            ),
                        )
                    except asyncio.CancelledError:
                        logger.warning(
                            "%s was cancelled (CancelledError)", func.__name__
                        )
                        if raise_on_error:
                            logger.error("%s re-raising CancelledError", func.__name__)
                            raise
                        logger.info(
                            "%s returning default for CancelledError", func.__name__
                        )
                        return cast(R, error_return)
                    except Exception as err:
                        rate_limit_delay = get_rate_limit_retry_after(err)
                        if (
                            rate_limit_delay is not None
                            and remaining_transient_retries > 0
                        ):
                            logger.warning(
                                "%s rate-limited on attempt %d; sleeping %.2fs then retrying",
                                func.__name__,
                                attempt,
                                rate_limit_delay,
                            )
                            remaining_transient_retries -= 1
                            await asyncio.sleep(rate_limit_delay)
                            continue
                        if remaining_transient_retries > 0 and is_transient_error(err):
                            backoff = TRANSIENT_BACKOFF_SECONDS * attempt
                            logger.warning(
                                "%s transient failure on attempt %d; retrying in %ds: %s",
                                func.__name__,
                                attempt,
                                backoff,
                                err,
                            )
                            remaining_transient_retries -= 1
                            await asyncio.sleep(backoff)
                            continue
                        logger.info(
                            "%s generic error (non-retry), handing off", func.__name__
                        )
                        return cast(
                            R,
                            handle_generic_error(
                                err,
                                func.__name__,
                                log_args,
                                log_kwargs,
                                raise_on_error,
                                error_return,
                            ),
                        )

            logger.info("handle_exceptions: wrapped async %s", func.__name__)
            return cast(Callable[P, R], async_wrapper)

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log_args = list(args)
            log_kwargs = dict(kwargs)
            if callable(default_return_value):
                logger.info("%s computing default_return_value callable", func.__name__)
                error_return = default_return_value(*args, **kwargs)
            else:
                logger.info("%s using static default_return_value", func.__name__)
                error_return = default_return_value
            remaining_transient_retries = TRANSIENT_MAX_ATTEMPTS - 1
            attempt = 0
            while True:
                attempt += 1
                try:
                    logger.info("%s invoking attempt %d", func.__name__, attempt)
                    return func(*args, **kwargs)
                except requests.HTTPError as err:
                    rate_limit_delay = get_rate_limit_retry_after(err)
                    if rate_limit_delay is not None and remaining_transient_retries > 0:
                        logger.warning(
                            "%s rate-limited via HTTPError on attempt %d; sleeping %.2fs then retrying",
                            func.__name__,
                            attempt,
                            rate_limit_delay,
                        )
                        remaining_transient_retries -= 1
                        time.sleep(rate_limit_delay)
                        continue
                    logger.info(
                        "%s HTTPError not rate-limited or retries exhausted; handing off",
                        func.__name__,
                    )
                    result, retried = handle_http_error(
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
                        logger.info("%s HTTPError retry result ready", func.__name__)
                        return cast(R, result)
                    logger.info("%s HTTPError returning non-retry", func.__name__)
                    return cast(R, result)
                except json.JSONDecodeError as err:
                    logger.info("%s hit JSONDecodeError, handing off", func.__name__)
                    return cast(
                        R,
                        handle_json_error(
                            err,
                            func.__name__,
                            log_args,
                            log_kwargs,
                            raise_on_error,
                            error_return,
                        ),
                    )
                except Exception as err:
                    rate_limit_delay = get_rate_limit_retry_after(err)
                    if rate_limit_delay is not None and remaining_transient_retries > 0:
                        logger.warning(
                            "%s rate-limited on attempt %d; sleeping %.2fs then retrying",
                            func.__name__,
                            attempt,
                            rate_limit_delay,
                        )
                        remaining_transient_retries -= 1
                        time.sleep(rate_limit_delay)
                        continue
                    if remaining_transient_retries > 0 and is_transient_error(err):
                        backoff = TRANSIENT_BACKOFF_SECONDS * attempt
                        logger.warning(
                            "%s transient failure on attempt %d; retrying in %ds: %s",
                            func.__name__,
                            attempt,
                            backoff,
                            err,
                        )
                        remaining_transient_retries -= 1
                        time.sleep(backoff)
                        continue
                    logger.info(
                        "%s generic error (non-retry), handing off", func.__name__
                    )
                    return cast(
                        R,
                        handle_generic_error(
                            err,
                            func.__name__,
                            log_args,
                            log_kwargs,
                            raise_on_error,
                            error_return,
                        ),
                    )

        logger.info("handle_exceptions: returning sync wrapper for %s", func.__name__)
        return wrapper

    logger.info("handle_exceptions: returning decorator")
    return decorator

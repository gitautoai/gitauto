# pylint: disable=broad-exception-caught

# Standard imports
import time
from functools import wraps
from typing import Any, Callable, Tuple, TypeVar

# Third party imports
import logging
import requests

F = TypeVar("F", bound=Callable[..., Any])


def handle_exceptions(
    default_return_value: Any = None, raise_on_error: bool = False
) -> Callable[[F], F]:
    """https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#checking-the-status-of-your-rate-limit"""

    def decorator(func: F) -> F:
        @wraps(wrapped=func)
        def wrapper(*args: Tuple[Any, ...], **kwargs: Any):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as err:
                if (
                    err.response.status_code == 403
                    and "X-RateLimit-Reset" in err.response.headers
                ):
                    limit = int(err.response.headers["X-RateLimit-Limit"])
                    remaining = int(err.response.headers["X-RateLimit-Remaining"])
                    used = int(err.response.headers["X-RateLimit-Used"])
                    reset_timestamp = int(err.response.headers["X-RateLimit-Reset"])
                    current_timestamp = int(time.time())
                    wait_time = reset_timestamp - current_timestamp
                    err_msg = f"{func.__name__} encountered a GitHubRateLimitError: {err}. Retrying after {wait_time} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}"
                    logging.error(msg=err_msg)
                    time.sleep(wait_time + 5)  # 5 seconds is a buffer
                    return wrapper(*args, **kwargs)
            except (AttributeError, KeyError, TypeError, Exception) as err:
                error_msg = f"{func.__name__} encountered an {type(err).__name__}: {err}\nArgs: {args}\nKwargs: {kwargs}"
                logging.error(msg=error_msg)
                if raise_on_error:
                    raise
            return default_return_value

        return wrapper  # type: ignore

    return decorator

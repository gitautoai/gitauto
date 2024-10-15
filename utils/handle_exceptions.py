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
            truncated_kwargs = str({k: str(v)[:50] + '...' if len(str(v)) > 50 else v for k, v in kwargs.items()})
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as err:
                reason: str | Any = err.response.reason
                text: str | Any = err.response.text

                if err.response.status_code in {403, 429}:
                    limit = int(err.response.headers["X-RateLimit-Limit"])
                    remaining = int(err.response.headers["X-RateLimit-Remaining"])
                    used = int(err.response.headers["X-RateLimit-Used"])

                    # Check if the primary rate limit has been exceeded
                    if remaining == 0:
                        reset_ts = int(err.response.headers.get("X-RateLimit-Reset", 0))
                        current_ts = int(time.time())
                        wait_time = reset_ts - current_ts
                        err_msg = f"{func.__name__} encountered a GitHubPrimaryRateLimitError: {err}. Retrying after {wait_time} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
                        logging.warning(msg=err_msg)
                        time.sleep(wait_time + 5)  # 5 seconds is a buffer
                        return wrapper(*args, **kwargs)

                    # Check if the secondary rate limit has been exceeded
                    if "exceeded a secondary rate limit" in err.response.text.lower():
                        retry_after = int(err.response.headers.get("Retry-After", 60))
                        err_msg = f"{func.__name__} encountered a GitHubSecondaryRateLimitError: {err}. Retrying after {retry_after} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
                        logging.warning(msg=err_msg)
                        time.sleep(retry_after)
                        return wrapper(*args, **kwargs)

                    # Otherwise, log the error and return the default return value
                    err_msg = f"{func.__name__} encountered an HTTPError: {err}. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}"
                    logging.error(msg=err_msg)
                    if raise_on_error:
                        raise

                # Ex) 409: Conflict, 422: Unprocessable Entity (No changes made), and etc.
                else:
                    err_msg = f"{func.__name__} encountered an HTTPError: {err}\nArgs: {args}\nKwargs: {truncated_kwargs}. Reason: {reason}. Text: {text}"
                    logging.error(msg=err_msg)
                if raise_on_error:
                    raise

            # Catch all other exceptions
            except (AttributeError, KeyError, TypeError, Exception) as err:
                error_msg = f"{func.__name__} encountered an {type(err).__name__}: {err}\nArgs: {args}\nKwargs: {truncated_kwargs}"
                logging.error(msg=error_msg)
                if raise_on_error:
                    raise
            return default_return_value

        return wrapper  # type: ignore

    return decorator

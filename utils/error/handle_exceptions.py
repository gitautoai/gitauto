# pylint: disable=broad-exception-caught

# Standard imports
from functools import wraps
import json
import logging
import time
from typing import Any, Callable, Tuple, TypeVar

# Third party imports
import requests

F = TypeVar("F", bound=Callable[..., Any])


def handle_exceptions(
    default_return_value: Any = None,
    raise_on_error: bool = False,
    api_type: str = "github",  # "github" or "google"
) -> Callable[[F], F]:
    """https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#checking-the-status-of-your-rate-limit"""

    def decorator(func: F) -> F:
        @wraps(wrapped=func)
        def wrapper(*args: Tuple[Any, ...], **kwargs: Any):
            log_args = list(args)
            log_kwargs = dict(kwargs)

            try:
                return func(*args, **kwargs)
            except requests.HTTPError as err:
                status_code: int = err.response.status_code

                # Skip logging for 500 Internal Server Error as it's usually a temporary issue and no meaningful information is available
                if status_code == 500:
                    if raise_on_error:
                        raise
                    return default_return_value

                reason: str | Any = err.response.reason
                text: str | Any = err.response.text
                print(f"reason: {reason}, text: {text}, status_code: {status_code}")

                if api_type == "github" and status_code in {403, 429}:
                    print(f"err.response.headers: {err.response.headers}")
                    limit = int(err.response.headers["X-RateLimit-Limit"])
                    remaining = int(err.response.headers["X-RateLimit-Remaining"])
                    used = int(err.response.headers["X-RateLimit-Used"])

                    # Check if the primary rate limit has been exceeded
                    if remaining == 0:
                        reset_ts = int(err.response.headers.get("X-RateLimit-Reset", 0))
                        current_ts = int(time.time())
                        wait_time = reset_ts - current_ts
                        if wait_time <= 0:
                            wait_time = 1  # Rate limit already reset, minimal wait
                        else:
                            wait_time = wait_time + 5  # 5 seconds is a buffer
                        err_msg = f"{func.__name__} encountered a GitHubPrimaryRateLimitError: {err}. Retrying after {wait_time} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}\n\n"
                        logging.warning(msg=err_msg)
                        time.sleep(wait_time)
                        return wrapper(*args, **kwargs)

                    # Check if the secondary rate limit has been exceeded
                    if "exceeded a secondary rate limit" in err.response.text.lower():
                        retry_after = int(err.response.headers.get("Retry-After", 60))
                        err_msg = f"{func.__name__} encountered a GitHubSecondaryRateLimitError: {err}. Retrying after {retry_after} seconds. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}\n\n"
                        logging.warning(msg=err_msg)
                        time.sleep(retry_after)
                        return wrapper(*args, **kwargs)

                    # Otherwise, log the error and return the default return value
                    err_msg = f"{func.__name__} encountered an HTTPError: {err}. Limit: {limit}, Remaining: {remaining}, Used: {used}. Reason: {reason}. Text: {text}\n\n"
                    logging.error(msg=err_msg)
                    if raise_on_error:
                        raise

                elif api_type == "google" and status_code == 429:
                    err_msg = f"Google Search Rate Limit in {func.__name__}()"
                    print(err_msg)
                    print(f"err.response.headers: {err.response.headers}")
                    raise
                    # retry_after = int(err.response.headers.get("Retry-After", 60))
                    # print(f"retry_after: {retry_after}")
                    # logging.warning(msg=err_msg)
                    # time.sleep(retry_after)
                    # return wrapper(*args, **kwargs)

                # Ex) 409: Conflict, 422: Unprocessable Entity (No changes made), and etc.
                else:
                    err_msg = f"{func.__name__} encountered an HTTPError: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}\n\nReason: {reason}\n\nText: {text}\n\n"
                    logging.error(msg=err_msg)
                if raise_on_error:
                    raise

            except json.JSONDecodeError as err:
                # Get the raw response that caused the JSON decode error
                if hasattr(err, "doc"):
                    raw_response = err.doc
                else:
                    raw_response = "Raw response not available"

                err_msg = f"{func.__name__} encountered a JSONDecodeError: {err}\n\nRaw response: {raw_response}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}"
                logging.error(msg=err_msg)
                if raise_on_error:
                    raise

            # Catch all other exceptions
            except (AttributeError, KeyError, TypeError, Exception) as err:
                err_msg = f"{func.__name__} encountered an {type(err).__name__}: {err}\n\nArgs: {json.dumps(log_args, indent=2, default=str)}\n\nKwargs: {json.dumps(log_kwargs, indent=2, default=str)}"
                logging.error(msg=err_msg)
                if raise_on_error:
                    raise
            return default_return_value

        return wrapper

    return decorator

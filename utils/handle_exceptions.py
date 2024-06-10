from functools import wraps
import logging
from typing import Any, Callable, Tuple, TypeVar

F = TypeVar('F', bound=Callable[..., Any])


def handle_exceptions(default_return_value: Any = None, raise_on_error: bool = False) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(wrapped=func)
        def wrapper(*args: Tuple[Any, ...], **kwargs: Any):
            try:
                return func(*args, **kwargs)
            except AttributeError as err:
                logging.error("%s encountered an AttributeError: %s", func.__name__, err)
                if raise_on_error:
                    raise
            except KeyError as err:
                logging.error("%s encountered a KeyError: %s", func.__name__, err)
                if raise_on_error:
                    raise
            except TypeError as err:
                logging.error("%s encountered a TypeError: %s", func.__name__, err)
                if raise_on_error:
                    raise
            except Exception as err:  # pylint: disable=broad-except
                logging.error("%s encountered an Exception: %s", func.__name__, err)
                if raise_on_error:
                    raise
            return default_return_value
        return wrapper  # type: ignore
    return decorator

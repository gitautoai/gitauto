import functools
import inspect
import time

from utils.logging.logging_config import logger


def timer_decorator(func):
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
            return result

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
        return result

    return wrapper

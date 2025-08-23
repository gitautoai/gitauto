import functools
import inspect
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def timer_decorator(func):
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
            finally:
                end_time = time.time()
                logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
            return result

        return wrapper
    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                end_time = time.time()
                logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
            return result

        return wrapper

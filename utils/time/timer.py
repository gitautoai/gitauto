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
            result = await func(*args, **kwargs)
            end_time = time.time()
            logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
            return result

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.info("%s took %.2f seconds", func.__name__, end_time - start_time)
            return result

    return wrapper

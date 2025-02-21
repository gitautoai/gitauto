import time
import functools
import inspect


def timer_decorator(func):
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            print(f"\n{func.__name__} took {end_time - start_time:.2f} seconds")
            return result

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"\n{func.__name__} took {end_time - start_time:.2f} seconds")
            return result

    return wrapper

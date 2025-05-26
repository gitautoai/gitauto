import functools
import json
import logging
import time
from typing import Any, Callable, Optional, Union

import requests


def truncate_value(value: Any, max_length: int = 30) -> Any:
    """
    Recursively truncate string values in data structures.
    
    Args:
        value: The value to truncate (can be string, dict, list, tuple, or other)
        max_length: Maximum length for strings before truncation
        
    Returns:
        The value with strings truncated if they exceed max_length
    """
    if isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + "..."
        return value
    elif isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    elif isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    elif isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    else:
        return value


def handle_exceptions(
    default_return_value: Any = None,
    raise_on_error: bool = False,
    api_type: Optional[str] = None
) -> Callable:
    """
    Decorator to handle exceptions with optional rate limiting for GitHub and Google APIs.
    
    Args:
        default_return_value: Value to return when an exception occurs (if not raising)
        raise_on_error: Whether to raise the exception or return default value
        api_type: Type of API ("github" or "google") for special rate limit handling
        
    Returns:
        Decorated function with exception handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    
                    # Handle GitHub API rate limiting
                    if api_type == "github":
                        if status_code == 403 and "rate limit" in e.response.text.lower():
                            # Primary rate limit
                            reset_time = e.response.headers.get("X-RateLimit-Reset")
                            if reset_time:
                                wait_time = max(0, int(reset_time) - int(time.time()) + 5)
                            else:
                                wait_time = max(0, 3600 - int(time.time()) + 5)  # Default 1 hour
                            
                            logging.warning(f"GitHub primary rate limit hit. Waiting {wait_time} seconds.")
                            time.sleep(wait_time)
                            return wrapper(*args, **kwargs)  # Retry
                            
                        elif status_code == 429 and "secondary rate limit" in e.response.text.lower():
                            # Secondary rate limit
                            retry_after = e.response.headers.get("Retry-After", "60")
                            wait_time = int(retry_after)
                            
                            logging.warning(f"GitHub secondary rate limit hit. Waiting {wait_time} seconds.")
                            time.sleep(wait_time)
                            return wrapper(*args, **kwargs)  # Retry
                    
                    # Handle Google API rate limiting
                    elif api_type == "google" and status_code == 429:
                        if raise_on_error:
                            raise
                        return default_return_value
                    
                    # Handle other HTTP errors
                    if status_code == 500:
                        if raise_on_error:
                            raise
                        return default_return_value
                
                # Log and handle other HTTP errors
                truncated_args = truncate_value(args)
                truncated_kwargs = truncate_value(kwargs)
                logging.error(
                    f"HTTP error in {func.__name__}: {e}. "
                    f"Args: {truncated_args}, Kwargs: {truncated_kwargs}"
                )
                
                if raise_on_error:
                    raise
                return default_return_value
                
            except json.JSONDecodeError as e:
                truncated_args = truncate_value(args)
                truncated_kwargs = truncate_value(kwargs)
                doc_info = f" Doc: {truncate_value(e.doc)}" if hasattr(e, 'doc') else ""
                logging.error(
                    f"JSON decode error in {func.__name__}: {e}.{doc_info} "
                    f"Args: {truncated_args}, Kwargs: {truncated_kwargs}"
                )
                
                if raise_on_error:
                    raise
                return default_return_value
                
            except (AttributeError, KeyError, TypeError) as e:
                truncated_args = truncate_value(args)
                truncated_kwargs = truncate_value(kwargs)
                logging.error(
                    f"{type(e).__name__} in {func.__name__}: {e}. "
                    f"Args: {truncated_args}, Kwargs: {truncated_kwargs}"
                )
                
                if raise_on_error:
                    raise
                return default_return_value
                
            except Exception as e:
                truncated_args = truncate_value(args)
                truncated_kwargs = truncate_value(kwargs)
                logging.error(
                    f"Unexpected error in {func.__name__}: {e}. "
                    f"Args: {truncated_args}, Kwargs: {truncated_kwargs}"
                )
                
                if raise_on_error:
                    raise
                return default_return_value
                
        return wrapper
    return decorator
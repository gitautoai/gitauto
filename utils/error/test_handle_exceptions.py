import time
import logging
import unittest
from unittest.mock import patch, MagicMock, call
import requests
from requests.exceptions import HTTPError

from tests.constants import OWNER, REPO
from utils.error.handle_exceptions import handle_exceptions


def test_function():
    return "success"


def test_function_with_args(arg1, arg2):
    return f"{arg1}_{arg2}"


def test_function_with_kwargs(key1="value1", key2="value2"):
    return f"{key1}_{key2}"


def test_function_raises_http_error():
    response = requests.Response()
    response.status_code = 404
    raise HTTPError("Not Found", response=response)


def test_function_raises_attribute_error():
    raise AttributeError("Attribute not found")


def test_function_raises_key_error():
    raise KeyError("Key not found")


def test_function_raises_type_error():
    raise TypeError("Type error")


def test_function_raises_generic_exception():
    raise Exception("Generic exception")


def test_github_rate_limit():
    response = requests.Response()
    response.status_code = 403
    response.reason = "Forbidden"
    response.text = "API rate limit exceeded"
    response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 60)
    }
    raise HTTPError("API rate limit exceeded", response=response)


def test_github_secondary_rate_limit():
    response = requests.Response()
    response.status_code = 403
    response.reason = "Forbidden"
    response.text = "You have exceeded a secondary rate limit"
    response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4990",
        "X-RateLimit-Used": "10",
        "Retry-After": "30"
    }
    raise HTTPError("Secondary rate limit exceeded", response=response)


def test_google_rate_limit():
    response = requests.Response()
    response.status_code = 429
    response.reason = "Too Many Requests"
    response.text = "Rate limit exceeded"
    response.headers = {
        "Retry-After": "60"
    }
    raise HTTPError("Rate limit exceeded", response=response)


def test_successful_execution():
    decorated_func = handle_exceptions()(test_function)
    result = decorated_func()
    assert result == "success"


def test_successful_execution_with_args():
    decorated_func = handle_exceptions()(test_function_with_args)
    result = decorated_func("hello", "world")
    assert result == "hello_world"


def test_successful_execution_with_kwargs():
    decorated_func = handle_exceptions()(test_function_with_kwargs)
    result = decorated_func(key1="custom1", key2="custom2")
    assert result == "custom1_custom2"


@patch("time.sleep")
@patch("logging.warning")
def test_github_primary_rate_limit_retry(mock_warning, mock_sleep):
    # Set up the decorated function to raise a rate limit error on first call
    # and then succeed on second call
    decorated_func = handle_exceptions()(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch("utils.error.handle_exceptions.wrapper", side_effect=[
            HTTPError("API rate limit exceeded", response=MagicMock(
                status_code=403,
                reason="Forbidden",
                text="API rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Used": "5000",
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )),
            "success"
        ]):
            with patch.object(decorated_func, "__wrapped__", side_effect=test_github_rate_limit):
                result = decorated_func()
                assert result is None
                mock_warning.assert_called_once()
                mock_sleep.assert_called_once()


@patch("time.sleep")
@patch("logging.warning")
def test_github_secondary_rate_limit_retry(mock_warning, mock_sleep):
    decorated_func = handle_exceptions()(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch("utils.error.handle_exceptions.wrapper", side_effect=[
            HTTPError("Secondary rate limit exceeded", response=MagicMock(
                status_code=403,
                reason="Forbidden",
                text="You have exceeded a secondary rate limit",
                headers={
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "4990",
                    "X-RateLimit-Used": "10",
                    "Retry-After": "30"
                }
            )),
            "success"
        ]):
            with patch.object(decorated_func, "__wrapped__", side_effect=test_github_secondary_rate_limit):
                result = decorated_func()
                assert result is None
                mock_warning.assert_called_once()
                mock_sleep.assert_called_once()


@patch("logging.error")
def test_github_other_http_error(mock_error):
    decorated_func = handle_exceptions(default_return_value="default")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=HTTPError("Not Found", response=MagicMock(
            status_code=404,
            reason="Not Found",
            text="Resource not found",
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Used": "1"
            }
        ))):
            result = decorated_func()
            assert result == "default"
            mock_error.assert_called_once()


@patch("logging.error")
def test_github_http_error_raise_on_error(mock_error):
    decorated_func = handle_exceptions(raise_on_error=True)(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=HTTPError("Not Found", response=MagicMock(
            status_code=404,
            reason="Not Found",
            text="Resource not found",
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Used": "1"
            }
        ))):
            try:
                decorated_func()
                assert False, "Expected HTTPError to be raised"
            except HTTPError:
                mock_error.assert_called_once()


@patch("logging.error")
def test_google_rate_limit_error(mock_error):
    decorated_func = handle_exceptions(api_type="google")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=HTTPError("Rate limit exceeded", response=MagicMock(
            status_code=429,
            reason="Too Many Requests",
            text="Rate limit exceeded",
            headers={
                "Retry-After": "60"
            }
        ))):
            try:
                decorated_func()
                assert False, "Expected HTTPError to be raised"
            except HTTPError:
                pass


@patch("logging.error")
def test_attribute_error(mock_error):
    decorated_func = handle_exceptions(default_return_value="default")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=AttributeError("Attribute not found")):
            result = decorated_func()
            assert result == "default"
            mock_error.assert_called_once()


@patch("logging.error")
def test_key_error(mock_error):
    decorated_func = handle_exceptions(default_return_value="default")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=KeyError("Key not found")):
            result = decorated_func()
            assert result == "default"
            mock_error.assert_called_once()


@patch("logging.error")
def test_type_error(mock_error):
    decorated_func = handle_exceptions(default_return_value="default")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=TypeError("Type error")):
            result = decorated_func()
            assert result == "default"
            mock_error.assert_called_once()


@patch("logging.error")
def test_generic_exception(mock_error):
    decorated_func = handle_exceptions(default_return_value="default")(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=Exception("Generic exception")):
            result = decorated_func()
            assert result == "default"
            mock_error.assert_called_once()


@patch("logging.error")
def test_exception_raise_on_error(mock_error):
    decorated_func = handle_exceptions(raise_on_error=True)(test_function)
    
    with patch.object(test_function, "__name__", "test_function"):
        with patch.object(decorated_func, "__wrapped__", side_effect=Exception("Generic exception")):
            try:
                decorated_func()
                assert False, "Expected Exception to be raised"
            except Exception:
                mock_error.assert_called_once()


def test_real_github_api_call():
    @handle_exceptions(default_return_value={"default": True})
    def get_nonexistent_repo():
        response = requests.get(
            f"https://api.github.com/repos/{OWNER}/nonexistent-repo-{int(time.time())}"
        )
        response.raise_for_status()
        return response.json()
    
    result = get_nonexistent_repo()
    assert result == {"default": True}
import json
import logging
import time
from unittest.mock import Mock, patch

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions, truncate_value


def test_truncate_value_string_short():
    result = truncate_value("short")
    assert result == "short"


def test_truncate_value_string_long():
    long_string = "a" * 50
    result = truncate_value(long_string)
    assert result == "a" * 30 + "..."


def test_truncate_value_string_custom_length():
    long_string = "a" * 20
    result = truncate_value(long_string, max_length=10)
    assert result == "a" * 10 + "..."


def test_truncate_value_dict():
    test_dict = {"key1": "a" * 50, "key2": "short"}
    result = truncate_value(test_dict)
    assert result == {"key1": "a" * 30 + "...", "key2": "short"}


def test_truncate_value_list():
    test_list = ["a" * 50, "short"]
    result = truncate_value(test_list)
    assert result == ["a" * 30 + "...", "short"]


def test_truncate_value_tuple():
    test_tuple = ("a" * 50, "short")
    result = truncate_value(test_tuple)
    assert result == ("a" * 30 + "...", "short")


def test_truncate_value_other_types():
    assert truncate_value(123) == 123
    assert truncate_value(None) == None
    assert truncate_value(True) == True


def test_truncate_value_nested_structures():
    nested_dict = {
        "level1": {
            "level2": ["a" * 50, ("b" * 50, "c" * 50)]
        }
    }
    result = truncate_value(nested_dict)
    expected = {
        "level1": {
            "level2": ["a" * 30 + "...", ("b" * 30 + "...", "c" * 30 + "...")]
        }
    }
    assert result == expected


def test_handle_exceptions_success():
    @handle_exceptions()
    def test_func():
        return "success"
    
    result = test_func()
    assert result == "success"


def test_handle_exceptions_with_args_kwargs():
    @handle_exceptions()
    def test_func(arg1, arg2, kwarg1=None):
        return f"{arg1}-{arg2}-{kwarg1}"
    
    result = test_func("a", "b", kwarg1="c")
    assert result == "a-b-c"


def test_handle_exceptions_http_error_500_no_raise():
    mock_response = Mock()
    mock_response.status_code = 500
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"


def test_handle_exceptions_http_error_500_raise():
    mock_response = Mock()
    mock_response.status_code = 500
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


@patch('time.sleep')
@patch('time.time')
@patch('logging.warning')
def test_handle_exceptions_github_primary_rate_limit(mock_warning, mock_time, mock_sleep):
    mock_time.return_value = 1000
    
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1060"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions(api_type="github")
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise http_error
        return "success"
    
    result = test_func()
    assert result == "success"
    mock_sleep.assert_called_once_with(65)
    mock_warning.assert_called_once()


@patch('time.sleep')
@patch('time.time')
def test_handle_exceptions_github_rate_limit_with_default_reset(mock_time, mock_sleep):
    mock_time.return_value = 1000
    
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions(api_type="github")
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise http_error
        return "success"
    
    result = test_func()
    assert result == "success"
    mock_sleep.assert_called_once_with(-995)


@patch('time.sleep')
@patch('logging.warning')
def test_handle_exceptions_github_secondary_rate_limit(mock_warning, mock_sleep):
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "You have exceeded a secondary rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900",
        "Retry-After": "30"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions(api_type="github")
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise http_error
        return "success"
    
    result = test_func()
    assert result == "success"
    mock_sleep.assert_called_once_with(30)
    mock_warning.assert_called_once()


@patch('time.sleep')
def test_handle_exceptions_github_secondary_rate_limit_default_retry(mock_sleep):
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "You have exceeded a secondary rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions(api_type="github")
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise http_error
        return "success"
    
    result = test_func()
    assert result == "success"
    mock_sleep.assert_called_once_with(60)


@patch('logging.error')
def test_handle_exceptions_github_other_error_no_raise(mock_error):
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_github_other_error_raise(mock_error):
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_github_429_status_no_secondary_rate_limit(mock_error):
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Regular rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


def test_handle_exceptions_google_rate_limit():
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {"Retry-After": "60"}
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="google")
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


@patch('logging.error')
def test_handle_exceptions_other_http_error_no_raise(mock_error):
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Conflict occurred"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_other_http_error_raise(mock_error):
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Conflict occurred"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_json_decode_error_with_doc_no_raise(mock_error):
    json_error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
    json_error.doc = "bad json"
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise json_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_json_decode_error_with_doc_raise(mock_error):
    json_error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
    json_error.doc = "bad json"
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise json_error
    
    with pytest.raises(json.JSONDecodeError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_json_decode_error_without_doc_no_raise(mock_error):
    json_error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
    if hasattr(json_error, 'doc'):
        delattr(json_error, 'doc')
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise json_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_json_decode_error_without_doc_raise(mock_error):
    json_error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
    if hasattr(json_error, 'doc'):
        delattr(json_error, 'doc')
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise json_error
    
    with pytest.raises(json.JSONDecodeError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_attribute_error_no_raise(mock_error):
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise AttributeError("Attribute not found")
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_attribute_error_raise(mock_error):
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise AttributeError("Attribute not found")
    
    with pytest.raises(AttributeError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_key_error_no_raise(mock_error):
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise KeyError("Key not found")
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_key_error_raise(mock_error):
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise KeyError("Key not found")
    
    with pytest.raises(KeyError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_type_error_no_raise(mock_error):
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise TypeError("Type error")
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_type_error_raise(mock_error):
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise TypeError("Type error")
    
    with pytest.raises(TypeError):
        test_func()
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_generic_exception_no_raise(mock_error):
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise Exception("Generic error")
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_generic_exception_raise(mock_error):
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise Exception("Generic error")
    
    with pytest.raises(Exception):
        test_func()
    mock_error.assert_called_once()


def test_handle_exceptions_with_complex_args():
    long_string = "a" * 50
    complex_dict = {"key": "b" * 50}
    complex_list = ["c" * 50]
    
    @handle_exceptions(default_return_value="default")
    def test_func(arg1, arg2, kwarg1=None):
        raise ValueError("Test error")
    
    result = test_func(long_string, complex_dict, kwarg1=complex_list)
    assert result == "default"


def test_handle_exceptions_preserves_function_metadata():
    @handle_exceptions()
    def test_func():
        return "test"
    
    assert test_func.__name__ == "test_func"
import json
import logging
import time
from unittest.mock import Mock, patch

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions


def test_handle_exceptions_successful_execution():
    @handle_exceptions()
    def test_func(x, y):
        return x + y
    
    result = test_func(1, 2)
    assert result == 3


def test_handle_exceptions_with_default_return_value():
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise ValueError("test error")
    
    result = test_func()
    assert result == "default"


def test_handle_exceptions_http_error_500_no_raise():
    mock_response = Mock()
    mock_response.status_code = 500
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(default_return_value="default_500")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default_500"


def test_handle_exceptions_http_error_500_with_raise():
    mock_response = Mock()
    mock_response.status_code = 500
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


def test_handle_exceptions_github_403_primary_rate_limit():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 10)
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
    
    with patch('time.sleep') as mock_sleep, \
         patch('logging.warning') as mock_warning:
        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once()
        mock_warning.assert_called_once()


def test_handle_exceptions_github_429_primary_rate_limit():
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 10)
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
    
    with patch('time.sleep') as mock_sleep, \
         patch('logging.warning') as mock_warning:
        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once()
        mock_warning.assert_called_once()


def test_handle_exceptions_github_secondary_rate_limit():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "You have exceeded a secondary rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900",
        "Retry-After": "60"
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
    
    with patch('time.sleep') as mock_sleep, \
         patch('logging.warning') as mock_warning:
        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once_with(60)
        mock_warning.assert_called_once()


def test_handle_exceptions_github_secondary_rate_limit_default_retry():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "You have EXCEEDED A SECONDARY RATE LIMIT"
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
    
    with patch('time.sleep') as mock_sleep, \
         patch('logging.warning') as mock_warning:
        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once_with(60)
        mock_warning.assert_called_once()


def test_handle_exceptions_github_other_error_no_raise():
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
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "default"
        mock_error.assert_called_once()


def test_handle_exceptions_github_other_error_with_raise():
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
    
    with patch('logging.error') as mock_error:
        with pytest.raises(requests.exceptions.HTTPError):
            test_func()
        mock_error.assert_called_once()


def test_handle_exceptions_google_429_error():
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


def test_handle_exceptions_other_http_error_no_raise():
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Resource conflict"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(default_return_value="conflict_default")
    def test_func(arg1, arg2, kwarg1=None):
        raise http_error
    
    with patch('logging.error') as mock_error:
        result = test_func("test_arg", 123, kwarg1="test_kwarg")
        assert result == "conflict_default"
        mock_error.assert_called_once()


def test_handle_exceptions_other_http_error_with_raise():
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.reason = "Unprocessable Entity"
    mock_response.text = "Validation error"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise http_error
    
    with patch('logging.error') as mock_error:
        with pytest.raises(requests.exceptions.HTTPError):
            test_func()
        mock_error.assert_called_once()


def test_handle_exceptions_json_decode_error_with_doc():
    json_error = json.JSONDecodeError("test error", "invalid json", 0)
    json_error.doc = "invalid json content"
    
    @handle_exceptions(default_return_value="json_default")
    def test_func():
        raise json_error
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "json_default"
        mock_error.assert_called_once()


def test_handle_exceptions_json_decode_error_without_doc():
    json_error = json.JSONDecodeError("test error", "invalid json", 0)
    if hasattr(json_error, 'doc'):
        delattr(json_error, 'doc')
    
    @handle_exceptions(default_return_value="json_default")
    def test_func():
        raise json_error
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "json_default"
        mock_error.assert_called_once()


def test_handle_exceptions_json_decode_error_with_raise():
    json_error = json.JSONDecodeError("test error", "invalid json", 0)
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise json_error
    
    with patch('logging.error') as mock_error:
        with pytest.raises(json.JSONDecodeError):
            test_func()
        mock_error.assert_called_once()


def test_handle_exceptions_attribute_error():
    @handle_exceptions(default_return_value="attr_default")
    def test_func():
        raise AttributeError("test attribute error")
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "attr_default"
        mock_error.assert_called_once()


def test_handle_exceptions_key_error():
    @handle_exceptions(default_return_value="key_default")
    def test_func():
        raise KeyError("test key error")
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "key_default"
        mock_error.assert_called_once()


def test_handle_exceptions_type_error():
    @handle_exceptions(default_return_value="type_default")
    def test_func():
        raise TypeError("test type error")
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "type_default"
        mock_error.assert_called_once()


def test_handle_exceptions_generic_exception():
    @handle_exceptions(default_return_value="generic_default")
    def test_func():
        raise RuntimeError("test runtime error")
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "generic_default"
        mock_error.assert_called_once()


def test_handle_exceptions_generic_exception_with_raise():
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise ValueError("test value error")
    
    with patch('logging.error') as mock_error:
        with pytest.raises(ValueError):
            test_func()
        mock_error.assert_called_once()


def test_handle_exceptions_with_complex_args_and_kwargs():
    @handle_exceptions(default_return_value="complex_default")
    def test_func(*args, **kwargs):
        raise ValueError("test error")
    
    complex_dict = {"key1": "value1", "key2": {"nested": "value"}}
    complex_list = [1, 2, {"item": "value"}]
    
    with patch('logging.error') as mock_error:
        result = test_func("arg1", 123, complex_dict, complex_list, 
                          kwarg1="value", kwarg2=complex_dict)
        assert result == "complex_default"
        mock_error.assert_called_once()


def test_handle_exceptions_preserves_function_metadata():
    @handle_exceptions()
    def test_func():
        return "test"
    
    assert test_func.__name__ == "test_func"


def test_handle_exceptions_github_rate_limit_with_missing_headers():
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
    
    with patch('time.sleep') as mock_sleep, \
         patch('logging.warning') as mock_warning:
        result = test_func()
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once()
        mock_warning.assert_called_once()


def test_handle_exceptions_different_api_types():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="other", default_return_value="other_default")
    def test_func():
        raise http_error
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "other_default"
        mock_error.assert_called_once()


def test_handle_exceptions_google_api_with_non_429_status():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="google", default_return_value="google_default")
    def test_func():
        raise http_error
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "google_default"
        mock_error.assert_called_once()


def test_handle_exceptions_github_429_with_remaining_quota():
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "100",
        "X-RateLimit-Used": "4900"
    }
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", default_return_value="github_default")
    def test_func():
        raise http_error
    
    with patch('logging.error') as mock_error:
        result = test_func()
        assert result == "github_default"
        mock_error.assert_called_once()

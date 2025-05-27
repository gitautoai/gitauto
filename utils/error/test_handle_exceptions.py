import json
import logging
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions


def test_handle_exceptions_success():
    @handle_exceptions()
    def test_func():
        return "success"

    result = test_func()
    assert result == "success"


def test_handle_exceptions_with_args_kwargs():
    @handle_exceptions()
    def test_func(arg1, arg2, kwarg1=None, kwarg2=None):
        return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"

    result = test_func("a", "b", kwarg1="c", kwarg2="d")
    assert result == "a-b-c-d"


def test_handle_exceptions_500_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise mock_error
    
    result = test_func()
    assert result == "default"


def test_handle_exceptions_500_error_raise_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise mock_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


def test_handle_exceptions_github_rate_limit_primary():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Rate limit exceeded"
    mock_response.text = "API rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 10)  # 10 seconds from now
    }
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions()
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise mock_error
        return "success after retry"
    
    with patch("time.sleep") as mock_sleep:
        with patch("logging.warning") as mock_warning:
            result = test_func()
            
            assert mock_sleep.called
            assert mock_warning.called
            assert result == "success after retry"
            assert call_count == 2


def test_handle_exceptions_github_rate_limit_secondary():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Rate limit exceeded"
    mock_response.text = "You have exceeded a secondary rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
        "Retry-After": "30"
    }
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    call_count = 0
    
    @handle_exceptions()
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise mock_error
        return "success after retry"
    
    with patch("time.sleep") as mock_sleep:
        with patch("logging.warning") as mock_warning:
            result = test_func()
            
            assert mock_sleep.called
            assert mock_warning.called
            assert result == "success after retry"
            assert call_count == 2


def test_handle_exceptions_github_other_rate_limit_error():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Some other error"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4900",
        "X-RateLimit-Used": "100"
    }
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise mock_error
    
    with patch("logging.error") as mock_error_log:
        result = test_func()
        
        assert mock_error_log.called
        assert result == "default"


def test_handle_exceptions_github_rate_limit_raise_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Some other error"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4900",
        "X-RateLimit-Used": "100"
    }
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise mock_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


def test_handle_exceptions_google_rate_limit():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Some-Header": "value"}
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(api_type="google")
    def test_func():
        raise mock_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


def test_handle_exceptions_other_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Resource not found"
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise mock_error
    
    with patch("logging.error") as mock_error_log:
        result = test_func()
        
        assert mock_error_log.called
        assert result == "default"


def test_handle_exceptions_other_http_error_raise_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Resource not found"
    
    mock_error = requests.exceptions.HTTPError()
    mock_error.response = mock_response
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise mock_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()


def test_handle_exceptions_json_decode_error_with_doc():
    mock_error = json.JSONDecodeError("Expecting value", '{"invalid": json}', 0)
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise mock_error
    
    with patch("logging.error") as mock_error_log:
        result = test_func()
        
        assert mock_error_log.called
        assert result == "default"


def test_handle_exceptions_json_decode_error_without_doc():
    mock_error = MagicMock(spec=json.JSONDecodeError)
    # Remove the 'doc' attribute
    if hasattr(mock_error, "doc"):
        delattr(mock_error, "doc")
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise mock_error
    
    with patch("logging.error") as mock_error_log:
        result = test_func()
        
        assert mock_error_log.called
        assert result == "default"


def test_handle_exceptions_json_decode_error_raise_on_error():
    mock_error = json.JSONDecodeError("Expecting value", '{"invalid": json}', 0)
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise mock_error
    
    with pytest.raises(json.JSONDecodeError):
        test_func()


def test_handle_exceptions_other_exceptions():
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise ValueError("Test error")
    
    with patch("logging.error") as mock_error_log:
        result = test_func()
        
        assert mock_error_log.called
        assert result == "default"


def test_handle_exceptions_other_exceptions_raise_on_error():
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        test_func()


def test_handle_exceptions_with_complex_args():
    @handle_exceptions()
    def test_func(arg1, arg2):
        if arg1["key"] == "error":
            raise ValueError("Test error")
        return arg1["key"] + arg2[0]
    
    with patch("logging.error") as mock_error_log:
        result = test_func({"key": "error"}, ["value"])
        
        assert mock_error_log.called
        assert result is None
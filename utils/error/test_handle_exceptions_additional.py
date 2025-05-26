from unittest.mock import Mock, patch

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions, truncate_value


@patch('logging.error')
def test_handle_exceptions_http_error_without_response(mock_error):
    """Test HTTP error without response attribute"""
    http_error = requests.exceptions.HTTPError("Connection error")
    
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_http_error_without_response_raise(mock_error):
    """Test HTTP error without response attribute with raise_on_error=True"""
    http_error = requests.exceptions.HTTPError("Connection error")
    
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()
    mock_error.assert_called_once()


def test_truncate_value_empty_structures():
    """Test truncate_value with empty data structures"""
    assert truncate_value({}) == {}
    assert truncate_value([]) == []
    assert truncate_value(()) == ()


def test_truncate_value_mixed_nested():
    """Test truncate_value with mixed nested structures"""
    mixed_data = {
        "short_key": "short",
        "long_key": "a" * 50,
        "nested": {
            "list": ["b" * 40, "short"],
            "tuple": ("c" * 35, 123, None)
        },
        "numbers": [1, 2, 3],
        "boolean": True
    }
    
    result = truncate_value(mixed_data)
    expected = {
        "short_key": "short",
        "long_key": "a" * 30 + "...",
        "nested": {
            "list": ["b" * 30 + "...", "short"],
            "tuple": ("c" * 30 + "...", 123, None)
        },
        "numbers": [1, 2, 3],
        "boolean": True
    }
    
    assert result == expected


@patch('time.sleep')
@patch('time.time')
@patch('logging.warning')
def test_handle_exceptions_github_rate_limit_negative_wait_time(mock_warning, mock_time, mock_sleep):
    """Test GitHub rate limit with negative wait time calculation"""
    mock_time.return_value = 2000  # Current time is after reset time
    
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1500"  # Reset time in the past
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
    # Should sleep for max(0, 1500 - 2000 + 5) = max(0, -495) = 0
    mock_sleep.assert_called_once_with(5)
    mock_warning.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_value_error(mock_error):
    """Test handling of ValueError (not specifically handled, falls to generic Exception)"""
    @handle_exceptions(default_return_value="default")
    def test_func():
        raise ValueError("Invalid value")
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_value_error_raise(mock_error):
    """Test handling of ValueError with raise_on_error=True"""
    @handle_exceptions(raise_on_error=True)
    def test_func():
        raise ValueError("Invalid value")
    
    with pytest.raises(ValueError):
        test_func()
    mock_error.assert_called_once()


def test_handle_exceptions_no_exception():
    """Test decorator when no exception occurs"""
    @handle_exceptions(default_return_value="default")
    def test_func(x, y):
        return x + y
    
    result = test_func(1, 2)
    assert result == 3


def test_handle_exceptions_with_none_default():
    """Test decorator with None as default return value"""
    @handle_exceptions()  # default_return_value defaults to None
    def test_func():
        raise Exception("Test error")
    
    result = test_func()
    assert result is None


@patch('logging.error')
def test_handle_exceptions_github_403_non_rate_limit(mock_error):
    """Test GitHub 403 error that's not a rate limit"""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied - not rate limit"
    mock_response.headers = {}
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()


@patch('logging.error')
def test_handle_exceptions_github_429_non_secondary_rate_limit(mock_error):
    """Test GitHub 429 error that's not a secondary rate limit"""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Too many requests - not secondary rate limit"
    mock_response.headers = {}
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="github", default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"
    mock_error.assert_called_once()

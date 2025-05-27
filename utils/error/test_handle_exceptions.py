# Standard imports
import json
import time
from unittest.mock import Mock, patch

# Third party imports
import pytest
import requests

# Local imports
from utils.error.handle_exceptions import handle_exceptions


def test_handle_exceptions_successful_execution():
    """Test that successful function execution returns the result."""
    @handle_exceptions()
    def successful_function(x, y):
        return x + y
    
    result = successful_function(2, 3)
    assert result == 5


def test_handle_exceptions_default_return_value():
    """Test that default return value is returned on exception."""
    @handle_exceptions(default_return_value="default")
    def failing_function():
        raise ValueError("Test error")
    
    result = failing_function()
    assert result == "default"


def test_handle_exceptions_raise_on_error():
    """Test that exceptions are raised when raise_on_error=True."""
    @handle_exceptions(raise_on_error=True)
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()


def test_handle_exceptions_http_error_500_no_raise():
    """Test that 500 errors are handled silently when raise_on_error=False."""
    @handle_exceptions(default_return_value="default")
    def function_with_500_error():
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    result = function_with_500_error()
    assert result == "default"


def test_handle_exceptions_http_error_500_with_raise():
    """Test that 500 errors are raised when raise_on_error=True."""
    @handle_exceptions(raise_on_error=True)
    def function_with_500_error():
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with pytest.raises(requests.exceptions.HTTPError):
        function_with_500_error()


def test_handle_exceptions_github_primary_rate_limit():
    """Test GitHub primary rate limit handling."""
    @handle_exceptions(api_type="github")
    def function_with_rate_limit():
        response = Mock()
        response.status_code = 403
        response.reason = "Forbidden"
        response.text = "Rate limit exceeded"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": str(int(time.time()) + 10),
        }
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep") as mock_sleep:
        # Mock the function to succeed on second call
        call_count = 0
        original_func = function_with_rate_limit.__wrapped__
        
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_func()
            return "success"
        
        function_with_rate_limit.__wrapped__ = side_effect
        
        result = function_with_rate_limit()
        assert result == "success"
        mock_sleep.assert_called_once()
        # Should sleep for reset time + 5 seconds buffer
        assert mock_sleep.call_args[0][0] >= 5


def test_handle_exceptions_github_secondary_rate_limit():
    """Test GitHub secondary rate limit handling."""
    @handle_exceptions(api_type="github")
    def function_with_secondary_rate_limit():
        response = Mock()
        response.status_code = 403
        response.reason = "Forbidden"
        response.text = "You have exceeded a secondary rate limit"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Used": "4900",
            "Retry-After": "60",
        }
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep") as mock_sleep:
        # Mock the function to succeed on second call
        call_count = 0
        original_func = function_with_secondary_rate_limit.__wrapped__
        
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_func()
            return "success"
        
        function_with_secondary_rate_limit.__wrapped__ = side_effect
        
        result = function_with_secondary_rate_limit()
        assert result == "success"
        mock_sleep.assert_called_once_with(60)


def test_handle_exceptions_github_403_other():
    """Test GitHub 403 error that's not rate limit related."""
    @handle_exceptions(api_type="github", default_return_value="default")
    def function_with_403_error():
        response = Mock()
        response.status_code = 403
        response.reason = "Forbidden"
        response.text = "Access denied"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Used": "4900",
        }
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with patch("logging.error") as mock_log:
        result = function_with_403_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_github_429():
    """Test GitHub 429 error handling."""
    @handle_exceptions(api_type="github", default_return_value="default")
    def function_with_429_error():
        response = Mock()
        response.status_code = 429
        response.reason = "Too Many Requests"
        response.text = "Rate limit exceeded"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Used": "4900",
        }
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with patch("logging.error") as mock_log:
        result = function_with_429_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_google_429():
    """Test Google API 429 error handling."""
    @handle_exceptions(api_type="google")
    def function_with_google_429():
        response = Mock()
        response.status_code = 429
        response.reason = "Too Many Requests"
        response.text = "Quota exceeded"
        response.headers = {"Retry-After": "60"}
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with pytest.raises(requests.exceptions.HTTPError):
        function_with_google_429()


def test_handle_exceptions_other_http_errors():
    """Test handling of other HTTP errors (409, 422, etc.)."""
    @handle_exceptions(default_return_value="default")
    def function_with_409_error():
        response = Mock()
        response.status_code = 409
        response.reason = "Conflict"
        response.text = "Resource conflict"
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with patch("logging.error") as mock_log:
        result = function_with_409_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_json_decode_error():
    """Test handling of JSON decode errors."""
    @handle_exceptions(default_return_value="default")
    def function_with_json_error():
        error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
        error.doc = "bad json content"
        raise error
    
    with patch("logging.error") as mock_log:
        result = function_with_json_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_json_decode_error_no_doc():
    """Test handling of JSON decode errors without doc attribute."""
    @handle_exceptions(default_return_value="default")
    def function_with_json_error():
        raise json.JSONDecodeError("Invalid JSON", "bad json", 0)
    
    with patch("logging.error") as mock_log:
        result = function_with_json_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_attribute_error():
    """Test handling of AttributeError."""
    @handle_exceptions(default_return_value="default")
    def function_with_attribute_error():
        raise AttributeError("'NoneType' object has no attribute 'test'")
    
    with patch("logging.error") as mock_log:
        result = function_with_attribute_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_key_error():
    """Test handling of KeyError."""
    @handle_exceptions(default_return_value="default")
    def function_with_key_error():
        raise KeyError("missing_key")
    
    with patch("logging.error") as mock_log:
        result = function_with_key_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_type_error():
    """Test handling of TypeError."""
    @handle_exceptions(default_return_value="default")
    def function_with_type_error():
        raise TypeError("unsupported operand type(s)")
    
    with patch("logging.error") as mock_log:
        result = function_with_type_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_generic_exception():
    """Test handling of generic Exception."""
    @handle_exceptions(default_return_value="default")
    def function_with_generic_error():
        raise Exception("Something went wrong")
    
    with patch("logging.error") as mock_log:
        result = function_with_generic_error()
        assert result == "default"
        mock_log.assert_called_once()


def test_handle_exceptions_args_kwargs_truncation():
    """Test that args and kwargs are properly truncated in error messages."""
    @handle_exceptions(default_return_value="default")
    def function_with_long_args(long_string, **kwargs):
        raise ValueError("Test error")
    
    long_arg = "x" * 100  # Longer than default max_length of 30
    long_kwarg = "y" * 100
    
    with patch("logging.error") as mock_log:
        result = function_with_long_args(long_arg, long_kwarg=long_kwarg)
        assert result == "default"
        
        # Check that the error message contains truncated values
        error_call = mock_log.call_args[1]["msg"]
        assert "xxx..." in error_call  # Truncated arg
        assert "yyy..." in error_call  # Truncated kwarg


def test_handle_exceptions_preserves_function_metadata():
    """Test that the decorator preserves function metadata."""
    @handle_exceptions()
    def test_function():
        """Test function docstring."""
        return "test"
    
    assert test_function.__name__ == "test_function"
    assert test_function.__doc__ == "Test function docstring."


def test_handle_exceptions_github_rate_limit_missing_headers():
    """Test GitHub rate limit handling when headers are missing."""
    @handle_exceptions(api_type="github", default_return_value="default")
    def function_with_incomplete_headers():
        response = Mock()
        response.status_code = 403
        response.reason = "Forbidden"
        response.text = "Rate limit exceeded"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            # Missing X-RateLimit-Reset header
        }
        error = requests.exceptions.HTTPError()
        error.response = response
        raise error
    
    with patch("time.sleep") as mock_sleep:
        # Mock the function to succeed on second call
        call_count = 0
        original_func = function_with_incomplete_headers.__wrapped__
        
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_func()
            return "success"
        
        function_with_incomplete_headers.__wrapped__ = side_effect
        
        result = function_with_incomplete_headers()
        assert result == "success"
        mock_sleep.assert_called_once()
        # Should use default reset time of 0, resulting in sleep of 5 seconds
        assert mock_sleep.call_args[0][0] >= 5
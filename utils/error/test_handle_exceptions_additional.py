from unittest.mock import Mock, patch

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions, truncate_value


@patch('logging.error')
def test_handle_exceptions_github_429_status_code(mock_error):
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


@patch('logging.error')
def test_handle_exceptions_github_429_status_code_raise(mock_error):
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
    
    @handle_exceptions(api_type="github", raise_on_error=True)
    def test_func():
        raise http_error
    
    with pytest.raises(requests.exceptions.HTTPError):
        test_func()
    mock_error.assert_called_once()


def test_handle_exceptions_non_github_non_google_api():
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.reason = "Too Many Requests"
    mock_response.text = "Rate limit exceeded"
    
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    
    @handle_exceptions(api_type="other", default_return_value="default")
    def test_func():
        raise http_error
    
    result = test_func()
    assert result == "default"


def test_handle_exceptions_empty_collections():
    assert truncate_value(()) == ()
    assert truncate_value([]) == []
    assert truncate_value({}) == {}

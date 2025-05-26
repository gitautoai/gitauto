from unittest.mock import Mock, patch

import requests

from utils.error.handle_exceptions import handle_exceptions, truncate_value


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


def test_handle_exceptions_preserves_function_metadata():
    @handle_exceptions()
    def test_func():
        return "test"
    
    assert test_func.__name__ == "test_func"

# Standard imports
import os
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
import requests

# Local imports
from services.slack.slack import slack


def test_slack_url_not_set():
    """Test slack function when URL is not set."""
    with patch("services.slack.slack.URL", None):
        # The function should return None due to the handle_exceptions decorator
        # but we should verify the ValueError is raised internally
        result = slack("test message")
        assert result is None


def test_slack_with_url_set():
    """Test slack function when URL is set."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "test message"
    
    with patch("services.slack.slack.URL", test_url), \
         patch("services.slack.slack.requests.post") as mock_post:
        # Call the function
        slack(test_message)
        
        # Verify requests.post was called with the correct arguments
        mock_post.assert_called_once_with(
            test_url, 
            json={"text": test_message}, 
            timeout=120
        )


def test_slack_with_request_exception():
    """Test slack function when requests.post raises an exception."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "test message"
    
    with patch("services.slack.slack.URL", test_url), \
         patch("services.slack.slack.requests.post") as mock_post:
        # Make requests.post raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("Test exception")
        
        # Call the function - should return None due to handle_exceptions
        result = slack(test_message)
        
        # Verify the result is None
        assert result is None
        
        # Verify requests.post was called
        mock_post.assert_called_once()


def test_slack_with_http_error():
    """Test slack function when requests.post raises an HTTPError."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "test message"
    
    with patch("services.slack.slack.URL", test_url), \
         patch("services.slack.slack.requests.post") as mock_post:
        # Create a mock response with status code 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Error text"
        
        # Create an HTTPError with the mock response
        http_error = requests.exceptions.HTTPError("Test HTTP error")
        http_error.response = mock_response
        
        # Make requests.post raise the HTTPError
        mock_post.side_effect = http_error
        
        # Call the function - should return None due to handle_exceptions
        result = slack(test_message)
        
        # Verify the result is None
        assert result is None
        
        # Verify requests.post was called
        mock_post.assert_called_once()
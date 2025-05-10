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
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": ""}):
        with patch("services.slack.slack.URL", None):
            # Should return None due to handle_exceptions decorator
            result = slack("test message")
            assert result is None


def test_slack_success():
    """Test slack function with successful request."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}):
        with patch("services.slack.slack.URL", test_url):
            with patch("requests.post") as mock_post:
                mock_post.return_value = MagicMock(status_code=200)
                
                # Call the function
                result = slack(test_message)
                
                # Verify the function called requests.post with correct arguments
                mock_post.assert_called_once_with(
                    test_url, 
                    json={"text": test_message}, 
                    timeout=120
                )
                assert result is None


def test_slack_request_exception():
    """Test slack function when request raises an exception."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}):
        with patch("services.slack.slack.URL", test_url):
            with patch("requests.post") as mock_post:
                # Simulate a request exception
                mock_post.side_effect = requests.RequestException("Test exception")
                
                # Call the function - should return None due to handle_exceptions
                result = slack(test_message)
                
                # Verify the function called requests.post
                mock_post.assert_called_once()
                assert result is None


def test_slack_http_error():
    """Test slack function when request raises an HTTP error."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_message = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}):
        with patch("services.slack.slack.URL", test_url):
            with patch("requests.post") as mock_post:
                # Create a mock response with an error status
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
                mock_post.return_value = mock_response
                
                # Call the function - should return None due to handle_exceptions
                result = slack(test_message)
                
                # Verify the function called requests.post
                mock_post.assert_called_once()
                assert result is None
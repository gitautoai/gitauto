# Standard imports
import os
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
import requests

# Local imports
from services.slack.slack import slack


def test_slack_with_url_set():
    """Test slack function when URL is set."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_text = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}), \
         patch("services.slack.slack.URL", test_url), \
         patch("requests.post") as mock_post:
        
        # Call the function
        slack(test_text)
        
        # Verify the request was made with correct parameters
        mock_post.assert_called_once_with(
            test_url, 
            json={"text": test_text}, 
            timeout=120
        )


def test_slack_with_url_not_set():
    """Test slack function when URL is not set."""
    test_text = "Test message"
    
    # Ensure URL is None for this test
    with patch("services.slack.slack.URL", None), \
         patch("requests.post") as mock_post:
        
        # Call the function and expect ValueError
        with pytest.raises(ValueError) as excinfo:
            slack(test_text)
        
        # Verify the error message
        assert "SLACK_WEBHOOK_URL_NOTIFICATIONS is not set" in str(excinfo.value)
        
        # Verify requests.post was not called
        mock_post.assert_not_called()


def test_slack_with_request_exception():
    """Test slack function when requests.post raises an exception."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_text = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}), \
         patch("services.slack.slack.URL", test_url), \
         patch("requests.post") as mock_post:
        
        # Make requests.post raise an exception
        mock_post.side_effect = requests.RequestException("Connection error")
        
        # Call the function - it should handle the exception and return None
        result = slack(test_text)
        
        # Verify the result is None (default_return_value from handle_exceptions)
        assert result is None
        
        # Verify the request was attempted
        mock_post.assert_called_once()


def test_slack_with_timeout_exception():
    """Test slack function when requests.post raises a Timeout exception."""
    test_url = "https://hooks.slack.com/services/test/webhook"
    test_text = "Test message"
    
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": test_url}), \
         patch("services.slack.slack.URL", test_url), \
         patch("requests.post") as mock_post:
        
        # Make requests.post raise a Timeout exception
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        # Call the function - it should handle the exception and return None
        result = slack(test_text)
        
        # Verify the result is None (default_return_value from handle_exceptions)
        assert result is None
        
        # Verify the request was attempted
        mock_post.assert_called_once()

# Standard imports
import os
from unittest.mock import patch, MagicMock

# Third party imports
import pytest

# Local imports
from services.slack.slack import slack
from config import TIMEOUT


def test_slack_with_valid_url():
    """Test slack function with a valid URL."""
    # Setup
    test_text = "Test message"
    mock_url = "https://hooks.slack.com/services/test/webhook"
    
    # Mock the environment variable and requests.post
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": mock_url}), \
         patch("requests.post") as mock_post:
        # Execute
        slack(test_text)
        
        # Assert
        mock_post.assert_called_once_with(
            mock_url, 
            json={"text": test_text}, 
            timeout=TIMEOUT
        )


def test_slack_with_missing_url():
    """Test slack function when URL is not set."""
    # Setup
    test_text = "Test message"
    
    # Mock the environment variable to be None/empty
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": ""}), \
         patch("requests.post") as mock_post:
        # Execute and Assert
        with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL_NOTIFICATIONS is not set"):
            slack(test_text)
        
        # Verify requests.post was not called
        mock_post.assert_not_called()


def test_slack_with_request_exception():
    """Test slack function when requests.post raises an exception."""
    # Setup
    test_text = "Test message"
    mock_url = "https://hooks.slack.com/services/test/webhook"
    
    # Mock the environment variable and requests.post to raise an exception
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": mock_url}), \
         patch("requests.post", side_effect=Exception("Test exception")):
        # Execute
        result = slack(test_text)
        
        # Assert - the function should return None due to the handle_exceptions decorator
        assert result is None


def test_slack_with_http_error():
    """Test slack function when requests.post raises an HTTPError."""
    # Setup
    test_text = "Test message"
    mock_url = "https://hooks.slack.com/services/test/webhook"
    
    # Create a mock response with an HTTPError
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Not Found"
    mock_response.headers = {}
    
    # Create a mock HTTPError
    mock_http_error = MagicMock()
    mock_http_error.response = mock_response
    
    # Mock the environment variable and requests.post to raise an HTTPError
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": mock_url}), \
         patch("requests.post", side_effect=mock_http_error):
        # Execute
        result = slack(test_text)
        
        # Assert - the function should return None due to the handle_exceptions decorator
        assert result is None
# Standard imports
import os
from unittest.mock import patch

# Local imports
from services.slack.slack import slack
from config import TIMEOUT


def test_slack_integration_with_mocked_request():
    """
    Integration test for the slack function.
    
    This test mocks the actual HTTP request but tests the full function flow
    including environment variable access and request formatting.
    """
    # Setup
    test_text = "Integration test message"
    mock_url = "https://hooks.slack.com/services/test/webhook"
    
    # Mock the environment variable and requests.post
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": mock_url}), \
         patch("requests.post") as mock_post:
        # Execute
        slack(test_text)
        
        # Assert
        mock_post.assert_called_once()
        
        # Verify the request was made with the correct parameters
        args, kwargs = mock_post.call_args
        assert args[0] == mock_url
        assert kwargs["json"] == {"text": test_text}
        assert kwargs["timeout"] == TIMEOUT


def test_slack_integration_with_empty_message():
    """
    Integration test for the slack function with an empty message.
    
    Tests that the function handles empty messages correctly.
    """
    # Setup
    test_text = ""
    mock_url = "https://hooks.slack.com/services/test/webhook"
    
    # Mock the environment variable and requests.post
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": mock_url}), \
         patch("requests.post") as mock_post:
        # Execute
        slack(test_text)
        
        # Assert
        mock_post.assert_called_once()
        
        # Verify the request was made with the correct parameters
        args, kwargs = mock_post.call_args
        assert args[0] == mock_url
        assert kwargs["json"] == {"text": ""}
        assert kwargs["timeout"] == TIMEOUT
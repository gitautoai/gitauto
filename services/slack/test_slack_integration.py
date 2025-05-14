import os
import unittest
from unittest.mock import patch, MagicMock

import requests

from services.slack.slack import slack
from config import TIMEOUT


class TestSlackIntegration(unittest.TestCase):
    @patch("services.slack.slack.URL", "https://hooks.slack.com/services/test/webhook")
    @patch("requests.post")
    def test_slack_integration_with_valid_url(self, mock_post):
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Execute
        result = slack("Integration test message")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/test/webhook", 
            json={"text": "Integration test message"}, 
            timeout=TIMEOUT
        )
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {"SLACK_WEBHOOK_URL_NOTIFICATIONS": "https://hooks.slack.com/services/test/webhook"})
    @patch("requests.post")
    def test_slack_integration_with_env_var(self, mock_post):
        # This test simulates the real environment variable being set
        # We need to reload the module to pick up the environment variable
        import importlib
        import services.slack.slack
        importlib.reload(services.slack.slack)
        
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Execute
        from services.slack.slack import slack as reloaded_slack
        result = reloaded_slack("Environment variable test")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/test/webhook", 
            json={"text": "Environment variable test"}, 
            timeout=TIMEOUT
        )
        self.assertIsNone(result)
        
        # Clean up by reloading the module again to restore original state
        importlib.reload(services.slack.slack)
    
    @patch("services.slack.slack.URL", "https://hooks.slack.com/services/test/webhook")
    @patch("requests.post")
    def test_slack_integration_with_long_message(self, mock_post):
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create a long message
        long_message = "A" * 10000
        
        # Execute
        result = slack(long_message)
        
        # Verify
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/test/webhook", 
            json={"text": long_message}, 
            timeout=TIMEOUT
        )
        self.assertIsNone(result)
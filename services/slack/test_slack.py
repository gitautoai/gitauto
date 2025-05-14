import os
import unittest
from unittest.mock import patch, MagicMock

import requests

from services.slack.slack import slack


class TestSlack(unittest.TestCase):
    @patch("services.slack.slack.URL", "https://example.com/webhook")
    @patch("requests.post")
    def test_slack_with_url_set(self, mock_post):
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Execute
        result = slack("Test message")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://example.com/webhook", 
            json={"text": "Test message"}, 
            timeout=120
        )
        self.assertIsNone(result)
    
    @patch("services.slack.slack.URL", None)
    def test_slack_with_url_not_set(self):
        # Execute and verify
        with self.assertRaises(ValueError) as context:
            slack("Test message")
        
        self.assertEqual(
            str(context.exception), 
            "SLACK_WEBHOOK_URL_NOTIFICATIONS is not set"
        )
    
    @patch("services.slack.slack.URL", "https://example.com/webhook")
    @patch("requests.post")
    def test_slack_with_request_exception(self, mock_post):
        # Setup
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Execute
        result = slack("Test message")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://example.com/webhook", 
            json={"text": "Test message"}, 
            timeout=120
        )
        self.assertIsNone(result)
    
    @patch("services.slack.slack.URL", "https://example.com/webhook")
    @patch("requests.post")
    def test_slack_with_http_error(self, mock_post):
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response
        mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        # Execute
        result = slack("Test message")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://example.com/webhook", 
            json={"text": "Test message"}, 
            timeout=120
        )
        self.assertIsNone(result)
    
    @patch("services.slack.slack.URL", "https://example.com/webhook")
    @patch("requests.post")
    def test_slack_with_empty_message(self, mock_post):
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Execute
        result = slack("")
        
        # Verify
        mock_post.assert_called_once_with(
            "https://example.com/webhook", 
            json={"text": ""}, 
            timeout=120
        )
        self.assertIsNone(result)
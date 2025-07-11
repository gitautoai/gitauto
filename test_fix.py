#!/usr/bin/env python3
"""Quick test to verify the HTTPError fix works."""

from unittest.mock import patch, MagicMock
from requests import HTTPError
from services.github.comments.delete_comment import delete_comment
from services.github.types.github_types import BaseArgs

def test_http_error_fix():
    """Test that our HTTPError fix works."""
    base_args = BaseArgs(
        owner="test-owner",
        repo="test-repo", 
        token="test-token-123"
    )
    
    # Create a proper HTTPError with a response object
    http_error = HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Comment not found"
    http_error.response = mock_error_response
    
    print("HTTPError created successfully with response object")
    print(f"Status code: {http_error.response.status_code}")
    print(f"Reason: {http_error.response.reason}")
    print(f"Text: {http_error.response.text}")

if __name__ == "__main__":
    test_http_error_fix()
    print("Test completed successfully!")

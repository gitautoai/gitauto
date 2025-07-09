# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch, Mock
from base64 import b64encode

# Third-party imports
import pytest
import requests

# Local imports
from utils.images.get_base64 import get_base64
from config import TIMEOUT, UTF8


@pytest.fixture
def mock_response():
    """Create a mock response object for successful requests."""
    response = Mock()
    response.content = b"fake_image_data"
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def mock_requests_get():
    """Mock requests.get function."""
    with patch("utils.images.get_base64.get") as mock_get:
        yield mock_get


class TestGetBase64:
    def test_get_base64_success(self, mock_requests_get, mock_response):
        """Test successful base64 encoding of image data."""
        # Setup
        test_url = "https://example.com/image.jpg"
        mock_requests_get.return_value = mock_response
        expected_base64 = b64encode(b"fake_image_data").decode(encoding=UTF8)
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == expected_base64
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)
        mock_response.raise_for_status.assert_called_once()

    def test_get_base64_with_different_image_data(self, mock_requests_get, mock_response):
        """Test base64 encoding with different image data."""
        # Setup
        test_url = "https://example.com/different.png"
        different_content = b"different_image_content_123"
        mock_response.content = different_content
        mock_requests_get.return_value = mock_response
        expected_base64 = b64encode(different_content).decode(encoding=UTF8)
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == expected_base64
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_with_empty_content(self, mock_requests_get, mock_response):
        """Test base64 encoding with empty image content."""
        # Setup
        test_url = "https://example.com/empty.jpg"
        mock_response.content = b""
        mock_requests_get.return_value = mock_response
        expected_base64 = b64encode(b"").decode(encoding=UTF8)
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == expected_base64
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_with_binary_image_data(self, mock_requests_get, mock_response):
        """Test base64 encoding with realistic binary image data."""
        # Setup
        test_url = "https://example.com/binary.jpg"
        # Simulate binary image data with various byte values
        binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])  # PNG header
        mock_response.content = binary_content
        mock_requests_get.return_value = mock_response
        expected_base64 = b64encode(binary_content).decode(encoding=UTF8)
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == expected_base64
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_http_error_returns_empty_string(self, mock_requests_get):
        """Test that HTTP errors return empty string due to handle_exceptions decorator."""
        # Setup
        test_url = "https://example.com/notfound.jpg"
        mock_response = Mock()
        # Create a proper HTTPError with response attribute
        http_error = requests.exceptions.HTTPError("404 Not Found")
        error_response = Mock()
        error_response.status_code = 404
        error_response.reason = "Not Found"
        error_response.text = "404 Not Found"
        http_error.response = error_response
        mock_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = mock_response
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == ""  # Default return value from handle_exceptions decorator
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_connection_error_returns_empty_string(self, mock_requests_get):
        """Test that connection errors return empty string due to handle_exceptions decorator."""
        # Setup
        test_url = "https://unreachable.example.com/image.jpg"
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == ""  # Default return value from handle_exceptions decorator
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_timeout_error_returns_empty_string(self, mock_requests_get):
        """Test that timeout errors return empty string due to handle_exceptions decorator."""
        # Setup
        test_url = "https://slow.example.com/image.jpg"
        mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == ""  # Default return value from handle_exceptions decorator
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_uses_correct_timeout(self, mock_requests_get, mock_response):
        """Test that the function uses the correct timeout value from config."""
        # Setup
        test_url = "https://example.com/image.jpg"
        mock_requests_get.return_value = mock_response
        
        # Execute
        get_base64(test_url)
        
        # Verify
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

    def test_get_base64_with_various_url_formats(self, mock_requests_get, mock_response):
        """Test that the function works with various URL formats."""
        # Setup
        test_urls = [
            "https://example.com/image.jpg",
            "http://example.com/path/to/image.png",
            "https://subdomain.example.com/images/photo.gif",
            "https://example.com/image.jpg?param=value&other=123",
        ]
        mock_requests_get.return_value = mock_response
        expected_base64 = b64encode(b"fake_image_data").decode(encoding=UTF8)
        
        for test_url in test_urls:
            # Execute
            result = get_base64(test_url)
            
            # Verify
            assert result == expected_base64
            
        # Verify all URLs were called
        assert mock_requests_get.call_count == len(test_urls)

    def test_get_base64_exception_handling_preserves_decorator_behavior(self, mock_requests_get):
        """Test that the handle_exceptions decorator behavior is preserved."""
        # Setup
        test_url = "https://example.com/image.jpg"
        mock_requests_get.side_effect = Exception("Unexpected error")
        
        # Execute
        result = get_base64(test_url)
        
        # Verify
        assert result == ""  # Default return value from handle_exceptions decorator
        mock_requests_get.assert_called_once_with(url=test_url, timeout=TIMEOUT)

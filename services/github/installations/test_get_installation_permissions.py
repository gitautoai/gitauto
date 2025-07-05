from unittest.mock import patch, MagicMock
import pytest
import requests
from requests import HTTPError

from config import GITHUB_API_URL, TIMEOUT
from services.github.installations.get_installation_permissions import get_installation_permissions


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    mock = MagicMock()
    mock.json.return_value = {
        "permissions": {
            "issues": "write",
            "pull_requests": "write",
            "contents": "read",
            "metadata": "read"
        }
    }
    mock.raise_for_status.return_value = None
    return mock


@pytest.fixture
def mock_headers():
    """Fixture to provide mocked headers."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def test_get_installation_permissions_success(mock_response, mock_headers):
    """Test successful retrieval of installation permissions."""
    installation_id = 12345
    token = "test_token"
    expected_url = f"{GITHUB_API_URL}/app/installations/{installation_id}"
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        
        result = get_installation_permissions(installation_id, token)
        
        mock_create_headers.assert_called_once_with(token=token)
        mock_get.assert_called_once_with(url=expected_url, headers=mock_headers, timeout=TIMEOUT)
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
        
        assert result == {
            "issues": "write",
            "pull_requests": "write",
            "contents": "read",
            "metadata": "read"
        }


def test_get_installation_permissions_no_permissions_key(mock_headers):
    """Test when response doesn't contain permissions key."""
    installation_id = 12345
    token = "test_token"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 12345, "app_id": 67890}
    mock_response.raise_for_status.return_value = None
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        
        result = get_installation_permissions(installation_id, token)
        
        assert result == {}


def test_get_installation_permissions_empty_permissions(mock_headers):
    """Test when permissions key exists but is empty."""
    installation_id = 12345
    token = "test_token"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"permissions": {}}
    mock_response.raise_for_status.return_value = None
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        
        result = get_installation_permissions(installation_id, token)
        
        assert result == {}


def test_get_installation_permissions_http_error(mock_headers):
    """Test handling of HTTP errors."""
    installation_id = 12345
    token = "test_token"
    
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        
        result = get_installation_permissions(installation_id, token)
        
        # Should return default value due to @handle_exceptions decorator
        assert result == {}


def test_get_installation_permissions_request_exception(mock_headers):
    """Test handling of request exceptions."""
    installation_id = 12345
    token = "test_token"
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.side_effect = requests.RequestException("Connection error")
        
        result = get_installation_permissions(installation_id, token)
        
        # Should return default value due to @handle_exceptions decorator
        assert result == {}


def test_get_installation_permissions_json_decode_error(mock_headers):
    """Test handling of JSON decode errors."""
    installation_id = 12345
    token = "test_token"
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
         patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        
        result = get_installation_permissions(installation_id, token)
        
        # Should return default value due to @handle_exceptions decorator
        assert result == {}


def test_get_installation_permissions_with_different_installation_ids():
    """Test function with different installation ID values."""
    token = "test_token"
    test_cases = [1, 12345, 999999999]
    
    for installation_id in test_cases:
        expected_url = f"{GITHUB_API_URL}/app/installations/{installation_id}"
        
        with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
             patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
            
            mock_response = MagicMock()
            mock_response.json.return_value = {"permissions": {"test": "read"}}
            mock_response.raise_for_status.return_value = None
            
            mock_create_headers.return_value = {}
            mock_get.return_value = mock_response
            
            result = get_installation_permissions(installation_id, token)
            
            mock_get.assert_called_once_with(url=expected_url, headers={}, timeout=TIMEOUT)
            assert result == {"test": "read"}


def test_get_installation_permissions_with_different_tokens():
    """Test function with different token values."""
    installation_id = 12345
    test_tokens = ["token1", "bearer_token_123", ""]
    
    for token in test_tokens:
        with patch("services.github.installations.get_installation_permissions.get") as mock_get, \
             patch("services.github.installations.get_installation_permissions.create_headers") as mock_create_headers:
            
            mock_response = MagicMock()
            mock_response.json.return_value = {"permissions": {}}
            mock_response.raise_for_status.return_value = None
            
            mock_create_headers.return_value = {}
            mock_get.return_value = mock_response
            
            get_installation_permissions(installation_id, token)
            
            mock_create_headers.assert_called_once_with(token=token)
import pytest
from unittest.mock import patch, MagicMock

from anthropic import Anthropic
from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


def test_get_anthropic_client():
    """Test that get_anthropic_client returns an Anthropic client with the correct API key."""
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY


def test_get_anthropic_client_with_mock():
    """Test get_anthropic_client using a mock to avoid actual client creation."""
    with patch('services.anthropic.client.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        client = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert client == mock_client


def test_get_anthropic_client_with_custom_params():
    """Test get_anthropic_client with custom parameters."""
    with patch('services.anthropic.client.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        client = get_anthropic_client(base_url="https://custom-api.anthropic.com")
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY, 
                                              base_url="https://custom-api.anthropic.com")
        assert client == mock_client


def test_get_anthropic_client_with_empty_api_key():
    """Test that get_anthropic_client handles empty API key appropriately."""
    with patch('services.anthropic.client.ANTHROPIC_API_KEY', ''):
        with pytest.raises(ValueError, match="Anthropic API key is not set or empty"):
            get_anthropic_client()


def test_get_anthropic_client_with_none_api_key():
    """Test that get_anthropic_client handles None API key appropriately."""
    with patch('services.anthropic.client.ANTHROPIC_API_KEY', None):
        with pytest.raises(ValueError, match="Anthropic API key is not set or empty"):
            get_anthropic_client()


def test_anthropic_client_configuration():
    """Test that the Anthropic client is configured with the correct parameters."""
    client = get_anthropic_client()
    
    # Verify client has expected attributes and methods
    assert hasattr(client, 'messages')
    assert hasattr(client, 'completions')
    assert callable(client.messages.create)

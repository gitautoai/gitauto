import pytest
from unittest.mock import patch, MagicMock
from anthropic import Anthropic

from services.anthropic.client import get_anthropic_client
from config import ANTHROPIC_API_KEY


def test_get_anthropic_client_returns_client_instance():
    """Test that get_anthropic_client returns an instance of Anthropic client."""
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY


def test_get_anthropic_client_with_mocked_anthropic():
    """Test get_anthropic_client with a mocked Anthropic class."""
    mock_client = MagicMock()
    
    with patch('services.anthropic.client.Anthropic', return_value=mock_client) as mock_anthropic:
        client = get_anthropic_client()
        
        # Verify Anthropic was instantiated with the correct API key
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert client == mock_client


def test_get_anthropic_client_with_missing_api_key():
    """Test get_anthropic_client behavior when API key is missing."""
    with patch('services.anthropic.client.ANTHROPIC_API_KEY', None), pytest.raises(TypeError):
        get_anthropic_client()
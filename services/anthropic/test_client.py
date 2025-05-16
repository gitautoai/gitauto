import pytest
from unittest.mock import patch, MagicMock

from anthropic import Anthropic
from services.anthropic.client import get_anthropic_client


def test_get_anthropic_client():
    with patch("services.anthropic.client.Anthropic") as mock_anthropic:
        mock_instance = MagicMock(spec=Anthropic)
        mock_anthropic.return_value = mock_instance
        
        client = get_anthropic_client()
        
        mock_anthropic.assert_called_once()
        assert client == mock_instance


def test_get_anthropic_client_with_api_key():
    with patch("services.anthropic.client.Anthropic") as mock_anthropic, \
         patch("services.anthropic.client.ANTHROPIC_API_KEY", "test_api_key"):
        mock_instance = MagicMock(spec=Anthropic)
        mock_anthropic.return_value = mock_instance
        
        client = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key="test_api_key")
        assert client == mock_instance
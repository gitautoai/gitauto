from unittest.mock import patch, MagicMock

import pytest
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


def test_get_anthropic_client_returns_client_instance():
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY


def test_get_anthropic_client_uses_api_key_from_config():
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", "test_api_key"):
        client = get_anthropic_client()
        assert client.api_key == "test_api_key"


def test_get_anthropic_client_creates_new_instance_each_call():
    client1 = get_anthropic_client()
    client2 = get_anthropic_client()
    assert client1 is not client2


@patch("services.anthropic.client.Anthropic")
def test_get_anthropic_client_passes_api_key_to_constructor(mock_anthropic):
    mock_instance = MagicMock()
    mock_anthropic.return_value = mock_instance
    
    client = get_anthropic_client()
    
    mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
    assert client == mock_instance


@patch("services.anthropic.client.Anthropic")
def test_get_anthropic_client_handles_empty_api_key(mock_anthropic):
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key="")


@patch("services.anthropic.client.Anthropic")
def test_get_anthropic_client_handles_none_api_key(mock_anthropic):
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
        get_anthropic_client()
        mock_anthropic.assert_called_once_with(api_key=None)
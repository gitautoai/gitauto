import pytest

from services.anthropic import client

from anthropic import Anthropic


def test_get_anthropic_client_instance_type():
    client_obj = client.get_anthropic_client()
    # Although we don't know the internals of Anthropic, we assume it's a class from the anthropic package
    assert isinstance(client_obj, Anthropic)


def test_get_anthropic_client_api_key(monkeypatch):
    dummy_key = "dummy_key"
    
    # Override the ANTHROPIC_API_KEY in the client module
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", dummy_key)

    # Create a dummy Anthropic class to capture the api_key parameter
    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)

    client_obj = client.get_anthropic_client()
    assert client_obj.api_key == dummy_key

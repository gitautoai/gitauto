from services.anthropic import client
import config


def test_get_anthropic_client_with_valid_key(monkeypatch):
    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key

    dummy_key = "dummy_test_key"
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", dummy_key)
    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)
    client_instance = client.get_anthropic_client()
    assert isinstance(client_instance, DummyAnthropic)
    assert client_instance.api_key == dummy_key


def test_get_anthropic_client_with_none_key(monkeypatch):
    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)
    client_instance = client.get_anthropic_client()
    assert isinstance(client_instance, DummyAnthropic)
    assert client_instance.api_key is None

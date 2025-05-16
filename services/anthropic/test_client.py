from services.anthropic.client import get_anthropic_client
import config

def dummy_Anthropic(api_key):
    class DummyClient:
        pass
    instance = DummyClient()
    instance.api_key = api_key
    return instance

def test_get_anthropic_client(monkeypatch):
    dummy_key = "dummy_key"
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", dummy_key)
    monkeypatch.setattr("services.anthropic.client.Anthropic", dummy_Anthropic)
    client = get_anthropic_client()
    assert client.api_key == dummy_key

from services.anthropic.client import get_anthropic_client
import config
import services.anthropic.client as client_mod
from types import SimpleNamespace

def DummyAnthropic(api_key):
    return SimpleNamespace(api_key=api_key)

def test_get_anthropic_client(monkeypatch):
    dummy_key = "dummy-key"
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", dummy_key)
    monkeypatch.setattr(client_mod, "Anthropic", DummyAnthropic)
    client_instance = get_anthropic_client()
    assert client_instance.api_key == dummy_key

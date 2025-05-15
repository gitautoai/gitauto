import pytest

from services.anthropic import client


class DummyAnthropic:
    def __init__(self, api_key):
        self.api_key = api_key


def test_get_anthropic_client(monkeypatch):
    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)
    dummy_key = "test_key"
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", dummy_key)
    anth_client = client.get_anthropic_client()
    assert isinstance(anth_client, DummyAnthropic)
    assert anth_client.api_key == dummy_key


def test_get_anthropic_client_with_none(monkeypatch):
    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", None)
    anth_client = client.get_anthropic_client()
    assert isinstance(anth_client, DummyAnthropic)
    assert anth_client.api_key is None

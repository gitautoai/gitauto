from services.anthropic import client
from config import ANTHROPIC_API_KEY
from anthropic import Anthropic
import pytest

def test_get_anthropic_client_normal():
    anth_client = client.get_anthropic_client()
    assert isinstance(anth_client, Anthropic)
    assert anth_client.api_key == ANTHROPIC_API_KEY

def test_get_anthropic_client_none(monkeypatch):
    monkeypatch.setattr("config.ANTHROPIC_API_KEY", None)
    anth_client = client.get_anthropic_client()
    assert isinstance(anth_client, Anthropic)
    assert anth_client.api_key is None

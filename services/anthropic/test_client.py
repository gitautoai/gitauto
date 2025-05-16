from services.anthropic import client
from config import ANTHROPIC_API_KEY

def test_get_anthropic_client(monkeypatch):
    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr(client, "Anthropic", DummyAnthropic)
    result = client.get_anthropic_client()
    assert isinstance(result, DummyAnthropic)
    assert result.api_key == ANTHROPIC_API_KEY

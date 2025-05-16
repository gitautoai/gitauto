def test_get_anthropic_client(monkeypatch):
    test_key = "test_api_key"
    class DummyAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr("services.anthropic.client.Anthropic", DummyAnthropic)
    monkeypatch.setattr("services.anthropic.client.ANTHROPIC_API_KEY", test_key)
    from services.anthropic.client import get_anthropic_client
    client = get_anthropic_client()
    assert client.api_key == test_key

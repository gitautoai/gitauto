from services.anthropic import client

def test_get_anthropic_client(monkeypatch):
    monkeypatch.setattr(client, "Anthropic", lambda **kwargs: "client-" + kwargs.get("api_key"))
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", "dummy-api-key")
    result = client.get_anthropic_client()
    assert result == "client-dummy-api-key"

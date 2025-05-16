from types import SimpleNamespace

def test_get_anthropic_client(monkeypatch):
    import services.anthropic.client as client
    client.ANTHROPIC_API_KEY = "dummy_api_key"
    called = {"called": False, "key": None}
    
    def fake_anthropic(api_key):
        called["called"] = True
        called["key"] = api_key
        return SimpleNamespace(api_key=api_key)

    monkeypatch.setattr(client, "Anthropic", fake_anthropic)
    instance = client.get_anthropic_client()
    assert called["called"] is True
    assert instance.api_key == "dummy_api_key"


def test_get_anthropic_client_empty(monkeypatch):
    import services.anthropic.client as client
    client.ANTHROPIC_API_KEY = ""

    def fake_anthropic(api_key):
        return SimpleNamespace(api_key=api_key)

    monkeypatch.setattr(client, "Anthropic", fake_anthropic)
    instance = client.get_anthropic_client()
    assert instance.api_key == ""

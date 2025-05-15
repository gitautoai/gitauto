from services.anthropic import client


def dummy_anthropic(api_key):
    return type('DummyAnthropic', (), {'api_key': api_key})()


def test_get_anthropic_client_success(monkeypatch):
    monkeypatch.setattr(client, 'Anthropic', dummy_anthropic)
    monkeypatch.setattr(client, 'ANTHROPIC_API_KEY', 'testkey')
    result = client.get_anthropic_client()
    assert result.api_key == 'testkey'


def test_get_anthropic_client_with_none_key(monkeypatch):
    monkeypatch.setattr(client, 'Anthropic', dummy_anthropic)
    monkeypatch.setattr(client, 'ANTHROPIC_API_KEY', None)
    result = client.get_anthropic_client()
    assert result.api_key is None

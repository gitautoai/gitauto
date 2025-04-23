from services.openai.init import create_openai_client
import config


class DummyOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_create_openai_client(monkeypatch):
    monkeypatch.setattr("services.openai.init.OpenAI", DummyOpenAI)
    test_api_key = "test_api_key"
    test_max_retries = 5
    test_org = "test_org"
    monkeypatch.setattr(config, "OPENAI_API_KEY", test_api_key)
    monkeypatch.setattr(config, "OPENAI_MAX_RETRIES", test_max_retries)
    monkeypatch.setattr(config, "OPENAI_ORG_ID", test_org)

    client = create_openai_client()
    assert isinstance(client, DummyOpenAI)
    assert client.kwargs["api_key"] == test_api_key
    assert client.kwargs["max_retries"] == test_max_retries
    assert client.kwargs["organization"] == test_org

from unittest.mock import patch

from services.google_ai.client import get_google_ai_client


@patch("services.google_ai.client.genai.Client")
def test_get_google_ai_client_returns_client(mock_client_class):
    mock_client_class.return_value = "mock-client"
    result = get_google_ai_client()
    assert result == "mock-client"
    mock_client_class.assert_called_once()


@patch("services.google_ai.client.genai.Client")
def test_get_google_ai_client_passes_api_key(mock_client_class):
    get_google_ai_client()
    call_kwargs = mock_client_class.call_args
    assert "api_key" in call_kwargs.kwargs

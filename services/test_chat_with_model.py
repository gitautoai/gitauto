from unittest.mock import MagicMock, patch

from constants.models import ClaudeModelId, GoogleModelId
from services.chat_with_model import chat_with_model
from services.llm_result import LlmResult


def _make_llm_result():
    return LlmResult(
        assistant_message={"role": "assistant", "content": "hi"},
        tool_calls=[],
        token_input=100,
        token_output=50,
        cost_usd=0.01,
    )


@patch("services.chat_with_model.chat_with_claude")
def test_routes_to_anthropic_for_opus(mock_claude: MagicMock):
    """Opus model should route to chat_with_claude."""
    mock_claude.return_value = _make_llm_result()

    result = chat_with_model(
        messages=[{"role": "user", "content": "test"}],
        system_content="system",
        tools=[],
        model_id=ClaudeModelId.OPUS_4_7,
        usage_id=1,
        created_by="test",
    )

    mock_claude.assert_called_once()
    assert result.assistant_message["role"] == "assistant"


@patch("services.chat_with_model.chat_with_claude")
def test_routes_to_anthropic_for_sonnet(mock_claude: MagicMock):
    """Sonnet model should route to chat_with_claude."""
    mock_claude.return_value = _make_llm_result()

    chat_with_model(
        messages=[{"role": "user", "content": "test"}],
        system_content="system",
        tools=[],
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=1,
        created_by="test",
    )

    mock_claude.assert_called_once()


@patch("services.chat_with_model.chat_with_google")
def test_routes_to_google_for_gemma(mock_google: MagicMock):
    """Gemma model should route to chat_with_google."""
    mock_google.return_value = _make_llm_result()

    chat_with_model(
        messages=[{"role": "user", "content": "test"}],
        system_content="system",
        tools=[],
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=1,
        created_by="test",
    )

    mock_google.assert_called_once()


@patch("services.chat_with_model.chat_with_google")
def test_routes_to_google_for_gemini_flash(mock_google: MagicMock):
    """Gemini Flash model should route to chat_with_google."""
    mock_google.return_value = _make_llm_result()

    chat_with_model(
        messages=[{"role": "user", "content": "test"}],
        system_content="system",
        tools=[],
        model_id=GoogleModelId.GEMINI_2_5_FLASH,
        usage_id=1,
        created_by="test",
    )

    mock_google.assert_called_once()

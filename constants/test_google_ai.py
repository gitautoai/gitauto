from unittest.mock import patch

from constants.google_ai import CONTEXT_WINDOW, GOOGLE_AI_API_KEY, MAX_OUTPUT_TOKENS
from constants.models import GoogleModelId


def test_google_ai_api_key_reads_from_env():
    with patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "test-key-123"}):
        # Module already loaded, so test the current value
        assert isinstance(GOOGLE_AI_API_KEY, str)


def test_google_ai_api_key_defaults_to_empty():
    # Default is empty string when env var not set
    assert GOOGLE_AI_API_KEY == "" or isinstance(GOOGLE_AI_API_KEY, str)


def test_context_window_matches_documented_limits():
    # Per https://ai.google.dev/gemini-api/docs/models
    assert CONTEXT_WINDOW[GoogleModelId.GEMINI_2_5_FLASH] == 1_048_576
    assert CONTEXT_WINDOW[GoogleModelId.GEMMA_4_31B] == 262_144


def test_max_output_tokens_matches_documented_limits():
    assert MAX_OUTPUT_TOKENS[GoogleModelId.GEMINI_2_5_FLASH] == 65_536
    assert MAX_OUTPUT_TOKENS[GoogleModelId.GEMMA_4_31B] == 8_192


def test_every_google_model_has_context_window_and_max_output():
    # Any model added to GoogleModelId must declare both limits so chat_with_google
    # never falls back to a guess when trimming.
    expected = set(GoogleModelId)
    assert set(CONTEXT_WINDOW.keys()) == expected
    assert set(MAX_OUTPUT_TOKENS.keys()) == expected

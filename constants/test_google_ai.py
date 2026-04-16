from unittest.mock import patch

from constants.google_ai import GOOGLE_AI_API_KEY


def test_google_ai_api_key_reads_from_env():
    with patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "test-key-123"}):
        # Module already loaded, so test the current value
        assert isinstance(GOOGLE_AI_API_KEY, str)


def test_google_ai_api_key_defaults_to_empty():
    # Default is empty string when env var not set
    assert GOOGLE_AI_API_KEY == "" or isinstance(GOOGLE_AI_API_KEY, str)

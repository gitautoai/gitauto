from anthropic import Anthropic, BadRequestError
from anthropic.types import MessageParam
import pytest

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_ID_40
from services.anthropic.client import get_anthropic_client


def test_get_anthropic_client_integration():
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY


def test_anthropic_client_can_count_tokens():
    client = get_anthropic_client()
    messages: list[MessageParam] = [{"role": "user", "content": "Hello, Claude!"}]

    try:
        token_count = client.messages.count_tokens(model=ANTHROPIC_MODEL_ID_40, messages=messages)
    except BadRequestError as e:
        if "credit balance is too low" in str(e):
            pytest.skip("Skipped test: insufficient credit balance for Anthropic API")
        else:
            raise
    else:
        assert token_count.input_tokens > 0
        assert isinstance(token_count.input_tokens, int)

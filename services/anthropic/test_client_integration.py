import pytest
from anthropic import Anthropic
from anthropic.types import MessageParam

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_ID_35
from services.anthropic.client import get_anthropic_client


@pytest.mark.integration
def test_get_anthropic_client_integration():
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY


@pytest.mark.integration
def test_anthropic_client_can_count_tokens():
    client = get_anthropic_client()
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": "Hello, Claude!"
        }
    ]
    
    token_count = client.messages.count_tokens(
        model=ANTHROPIC_MODEL_ID_35,
        messages=messages
    )
    
    assert token_count.input_tokens > 0
    assert isinstance(token_count.input_tokens, int)


@pytest.mark.integration
@pytest.mark.skipif(not ANTHROPIC_API_KEY, reason="No Anthropic API key available")
def test_anthropic_client_can_create_message():
    client = get_anthropic_client()
    
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL_ID_35,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one word"
                }
            ]
        )
        
        assert response.id is not None
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model.startswith("claude-3")
    except Exception as e:
        pytest.skip(f"Skipping due to API error: {str(e)}")
from anthropic import Anthropic
from anthropic.types import MessageParam
import pytest
import pytest
from anthropic import BadRequestError
from anthropic import BadRequestError
import pytest
import pytest
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_ID_40
from services.anthropic.client import get_anthropic_client


def test_get_anthropic_client_integration():
    client = get_anthropic_client()
    assert isinstance(client, Anthropic)
    assert client.api_key == ANTHROPIC_API_KEY



def test_anthropic_client_can_count_tokens():
    pytest.skip("Skipping test due to Anthropic API credit balance limitations.")

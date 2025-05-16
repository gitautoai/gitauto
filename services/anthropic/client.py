from anthropic import Anthropic
from config import ANTHROPIC_API_KEY


def get_anthropic_client() -> Anthropic:
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY is None:
        raise ValueError("Anthropic API key is not set or empty")
    return Anthropic(api_key=ANTHROPIC_API_KEY)

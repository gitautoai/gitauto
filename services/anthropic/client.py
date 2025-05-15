from anthropic import Anthropic
from config import ANTHROPIC_API_KEY


def get_anthropic_client() -> Anthropic:
    return Anthropic(api_key=ANTHROPIC_API_KEY)

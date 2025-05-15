from anthropic import Anthropic
import config


def get_anthropic_client() -> Anthropic:
    return Anthropic(api_key=config.ANTHROPIC_API_KEY)

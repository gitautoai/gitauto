from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


# https://docs.claude.com/en/docs/about-claude/pricing
# https://platform.openai.com/docs/pricing?latest-pricing=standard
@handle_exceptions(default_return_value=(0, 0), raise_on_error=False)
def calculate_costs(
    provider: str, model_id: str, input_tokens: int, output_tokens: int
):
    # Pricing per 1M tokens (input/output)
    pricing = {
        "claude": {
            "claude-opus-4-6": {"input": 5.00, "output": 25.00},
            "claude-opus-4-5": {"input": 5.00, "output": 25.00},
            "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
            "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
        },
        "google": {
            # https://ai.google.dev/gemini-api/docs/pricing
            "gemma-4-31b-it": {"input": 0.00, "output": 0.00},  # Free tier
            "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        },
        "openai": {
            "gpt-5.2": {"input": 1.75, "output": 14.00},
        },
    }

    provider_pricing = pricing.get(provider.lower(), {})
    model_pricing = provider_pricing.get(model_id)

    if not model_pricing:
        logger.warning("Unknown model %s for provider %s", model_id, provider)
        return 0, 0

    input_cost_usd = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost_usd = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost_usd, output_cost_usd

from utils.error.handle_exceptions import handle_exceptions


# https://docs.claude.com/en/docs/about-claude/pricing
# https://platform.openai.com/docs/pricing?latest-pricing=standard
@handle_exceptions(default_return_value=(0, 0), raise_on_error=False)
def calculate_costs(
    provider: str, model_id: str, input_tokens: int, output_tokens: int
):
    pricing = {
        "claude": {
            "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
            "claude-sonnet-4-0": {"input": 3.00, "output": 15.00},
            "claude-3-7-sonnet-latest": {"input": 3.00, "output": 15.00},
        },
        "openai": {
            "gpt-5": {"input": 1.25, "output": 10.00},
            "gpt-4.1": {"input": 2.00, "output": 8.00},
        },
    }

    provider_pricing = pricing.get(provider.lower(), {})
    model_pricing = provider_pricing.get(model_id)

    if not model_pricing:
        print(f"Warning: Unknown model {model_id} for provider {provider}")
        return 0, 0

    input_cost_usd = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost_usd = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost_usd, output_cost_usd

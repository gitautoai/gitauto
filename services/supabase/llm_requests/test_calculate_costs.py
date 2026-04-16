from config import OPENAI_MODEL_ID
from constants.models import GoogleModelId, MODEL_REGISTRY, ModelProvider
from services.supabase.llm_requests.calculate_costs import calculate_costs


def test_calculate_costs_claude_opus_46():
    input_cost, output_cost = calculate_costs("claude", "claude-opus-4-6", 1000, 500)
    expected_input = (1000 / 1_000_000) * 5.00
    expected_output = (500 / 1_000_000) * 25.00

    assert input_cost == expected_input
    assert output_cost == expected_output


def test_calculate_costs_claude_sonnet_46():
    input_cost, output_cost = calculate_costs("claude", "claude-sonnet-4-6", 1000, 500)
    expected_input = (1000 / 1_000_000) * 3.00
    expected_output = (500 / 1_000_000) * 15.00

    assert input_cost == expected_input
    assert output_cost == expected_output


def test_calculate_costs_claude_45():
    input_cost, output_cost = calculate_costs("claude", "claude-sonnet-4-5", 1000, 500)
    expected_input = (1000 / 1_000_000) * 3.00
    expected_output = (500 / 1_000_000) * 15.00

    assert input_cost == expected_input
    assert output_cost == expected_output


def test_calculate_costs_openai():
    input_cost, output_cost = calculate_costs("openai", "gpt-5.2", 1000, 500)
    expected_input = (1000 / 1_000_000) * 1.75
    expected_output = (500 / 1_000_000) * 14.00

    assert input_cost == expected_input
    assert output_cost == expected_output


def test_calculate_costs_unknown_provider():
    input_cost, output_cost = calculate_costs("unknown", "model", 1000, 500)
    assert input_cost == 0
    assert output_cost == 0


def test_calculate_costs_unknown_model():
    input_cost, output_cost = calculate_costs("claude", "unknown-model", 1000, 500)
    assert input_cost == 0
    assert output_cost == 0


def test_calculate_costs_zero_tokens():
    input_cost, output_cost = calculate_costs("claude", "claude-sonnet-4-6", 0, 0)
    assert input_cost == 0
    assert output_cost == 0


def test_all_models_have_pricing():
    """Every model in the registry must have a pricing entry (except free-tier models with zero cost)."""
    for model_id, info in MODEL_REGISTRY.items():
        provider = "claude" if info["provider"] == ModelProvider.CLAUDE else "google"
        input_cost, output_cost = calculate_costs(
            provider, model_id, 1_000_000, 1_000_000
        )
        # Gemma is free tier — zero cost is expected
        if model_id == GoogleModelId.GEMMA_4_31B:
            assert (
                input_cost == 0
            ), f"Expected zero input cost for free model: {model_id}"
            assert (
                output_cost == 0
            ), f"Expected zero output cost for free model: {model_id}"
        else:
            assert input_cost > 0, f"Missing pricing for {provider} model: {model_id}"
            assert output_cost > 0, f"Missing pricing for {provider} model: {model_id}"

    input_cost, output_cost = calculate_costs(
        "openai", OPENAI_MODEL_ID, 1_000_000, 1_000_000
    )
    assert input_cost > 0, f"Missing pricing for openai model: {OPENAI_MODEL_ID}"
    assert output_cost > 0, f"Missing pricing for openai model: {OPENAI_MODEL_ID}"

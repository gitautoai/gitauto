from config import OPENAI_MODEL_ID
from constants.claude import ClaudeModelId
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


def test_calculate_costs_claude_40():
    input_cost, output_cost = calculate_costs("claude", "claude-sonnet-4-0", 1000, 500)
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
    input_cost, output_cost = calculate_costs("claude", "claude-sonnet-4-0", 0, 0)
    assert input_cost == 0
    assert output_cost == 0


def test_all_models_have_pricing():
    """Every model constant must have a pricing entry."""
    for model in ClaudeModelId:
        input_cost, output_cost = calculate_costs("claude", model, 1_000_000, 1_000_000)
        assert input_cost > 0, f"Missing pricing for claude model: {model}"
        assert output_cost > 0, f"Missing pricing for claude model: {model}"

    input_cost, output_cost = calculate_costs(
        "openai", OPENAI_MODEL_ID, 1_000_000, 1_000_000
    )
    assert input_cost > 0, f"Missing pricing for openai model: {OPENAI_MODEL_ID}"
    assert output_cost > 0, f"Missing pricing for openai model: {OPENAI_MODEL_ID}"

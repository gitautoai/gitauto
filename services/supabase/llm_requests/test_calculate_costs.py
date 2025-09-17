from services.supabase.llm_requests.calculate_costs import calculate_costs


def test_calculate_costs_claude():
    input_cost, output_cost = calculate_costs(
        "claude", "claude-3-5-sonnet-latest", 1000, 500
    )
    expected_input = (1000 / 1_000_000) * 3.00
    expected_output = (500 / 1_000_000) * 15.00

    assert input_cost == expected_input
    assert output_cost == expected_output


def test_calculate_costs_openai():
    input_cost, output_cost = calculate_costs("openai", "gpt-5", 1000, 500)
    expected_input = (1000 / 1_000_000) * 1.25
    expected_output = (500 / 1_000_000) * 10.00

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
    input_cost, output_cost = calculate_costs(
        "claude", "claude-3-5-sonnet-latest", 0, 0
    )
    assert input_cost == 0
    assert output_cost == 0

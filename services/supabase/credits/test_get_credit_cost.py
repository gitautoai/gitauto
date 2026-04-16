from constants.models import (
    MAX_CREDIT_COST_USD,
    MODEL_REGISTRY,
    ClaudeModelId,
    GoogleModelId,
)
from services.supabase.credits.get_credit_cost import get_credit_cost


def test_returns_cost_for_known_model():
    for model_id, info in MODEL_REGISTRY.items():
        assert get_credit_cost(model_id) == info["credit_cost_usd"]


def test_returns_max_cost_for_none():
    assert get_credit_cost(None) == MAX_CREDIT_COST_USD


def test_opus_costs_8():
    assert get_credit_cost(ClaudeModelId.OPUS_4_6) == 8


def test_gemma_costs_2():
    assert get_credit_cost(GoogleModelId.GEMMA_4_31B) == 2

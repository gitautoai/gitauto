from constants.models import (
    MAX_CREDIT_COST_USD,
    MODEL_REGISTRY,
    ClaudeModelId,
    GoogleModelId,
)
from services.supabase.credits.get_credit_price import get_credit_price


def test_returns_cost_for_known_model():
    for model_id, info in MODEL_REGISTRY.items():
        assert get_credit_price(model_id) == info["credit_cost_usd"]


def test_returns_max_cost_for_none():
    assert get_credit_price(None) == MAX_CREDIT_COST_USD


def test_opus_costs_8():
    assert get_credit_price(ClaudeModelId.OPUS_4_6) == 8


def test_gemma_costs_2():
    assert get_credit_price(GoogleModelId.GEMMA_4_31B) == 2

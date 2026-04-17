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


def test_opus_47_costs_8():
    assert get_credit_price(ClaudeModelId.OPUS_4_7) == 8


def test_opus_46_costs_8():
    assert get_credit_price(ClaudeModelId.OPUS_4_6) == 8


def test_sonnet_46_costs_4():
    assert get_credit_price(ClaudeModelId.SONNET_4_6) == 4


def test_opus_45_costs_8():
    assert get_credit_price(ClaudeModelId.OPUS_4_5) == 8


def test_sonnet_45_costs_4():
    assert get_credit_price(ClaudeModelId.SONNET_4_5) == 4


def test_haiku_45_costs_2():
    assert get_credit_price(ClaudeModelId.HAIKU_4_5) == 2


def test_gemini_25_flash_costs_4():
    assert get_credit_price(GoogleModelId.GEMINI_2_5_FLASH) == 4


def test_gemma_costs_2():
    assert get_credit_price(GoogleModelId.GEMMA_4_31B) == 2

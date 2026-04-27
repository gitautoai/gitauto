from constants.models import (
    ClaudeModelId,
    DEFAULT_FREE_MODEL,
    DEFAULT_PAID_MODEL,
    FREE_TIER_MODELS,
    GoogleModelId,
    MODEL_REGISTRY,
    ModelProvider,
)


def test_all_model_ids_in_registry():
    """Every ModelId enum member must have an entry in MODEL_REGISTRY."""
    expected = {*ClaudeModelId, *GoogleModelId}
    assert set(MODEL_REGISTRY.keys()) == expected


def test_registry_has_required_fields():
    """Each registry entry has exactly the ModelInfo fields, all populated."""
    expected_fields = {
        "provider",
        "display_name",
        "credit_cost_usd",
        "user_selectable",
        "free_tier",
    }
    for model_id, info in MODEL_REGISTRY.items():
        assert set(info.keys()) == expected_fields, f"{model_id} fields mismatch"
        assert info["credit_cost_usd"] > 0, f"{model_id} has non-positive cost"


def test_affordable_models_are_cheap():
    """Affordable models should cost $4 or less."""
    for model_id in FREE_TIER_MODELS:
        cost = MODEL_REGISTRY[model_id]["credit_cost_usd"]
        assert cost <= 4, f"{model_id} costs ${cost}, expected <= $4"


def test_default_free_model_is_gemma_4_31b():
    assert DEFAULT_FREE_MODEL == GoogleModelId.GEMMA_4_31B


def test_default_paid_model_is_opus_47():
    assert DEFAULT_PAID_MODEL == ClaudeModelId.OPUS_4_7


def test_default_free_model_is_in_free_tier():
    assert DEFAULT_FREE_MODEL == GoogleModelId.GEMMA_4_31B
    assert FREE_TIER_MODELS == [GoogleModelId.GEMMA_4_31B]


def test_sonnet_4_6_and_gemini_2_5_flash_are_not_free_tier():
    """Sonnet 4.6 and Gemini 2.5 Flash were demoted from free_tier=True to False."""
    assert MODEL_REGISTRY[ClaudeModelId.SONNET_4_6]["free_tier"] is False
    assert MODEL_REGISTRY[GoogleModelId.GEMINI_2_5_FLASH]["free_tier"] is False


def test_providers_are_valid():
    """Every registry entry's provider is one of the two valid ModelProvider members."""
    actual_providers = {info["provider"] for info in MODEL_REGISTRY.values()}
    assert actual_providers == {ModelProvider.CLAUDE, ModelProvider.GOOGLE}


def test_google_models_count():
    """Registry has exactly two Google models: Gemini 2.5 Flash and Gemma 4 31B."""
    google_models = [
        m for m, r in MODEL_REGISTRY.items() if r["provider"] == ModelProvider.GOOGLE
    ]
    assert sorted(google_models) == sorted(
        [GoogleModelId.GEMINI_2_5_FLASH, GoogleModelId.GEMMA_4_31B]
    )


def test_anthropic_models_count():
    """Registry has exactly six Claude models."""
    anthropic_models = [
        m for m, r in MODEL_REGISTRY.items() if r["provider"] == ModelProvider.CLAUDE
    ]
    assert sorted(anthropic_models) == sorted(
        [
            ClaudeModelId.OPUS_4_7,
            ClaudeModelId.OPUS_4_6,
            ClaudeModelId.SONNET_4_6,
            ClaudeModelId.OPUS_4_5,
            ClaudeModelId.SONNET_4_5,
            ClaudeModelId.HAIKU_4_5,
        ]
    )


def test_opus_47_is_user_selectable():
    info = MODEL_REGISTRY[ClaudeModelId.OPUS_4_7]
    assert info["user_selectable"] is True
    assert info["credit_cost_usd"] == 8


def test_opus_46_is_fallback_only():
    info = MODEL_REGISTRY[ClaudeModelId.OPUS_4_6]
    assert info["user_selectable"] is False
    assert info["credit_cost_usd"] == 8

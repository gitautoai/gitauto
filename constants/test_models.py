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
    for model_id in [*ClaudeModelId, *GoogleModelId]:
        assert model_id in MODEL_REGISTRY, f"{model_id} missing from MODEL_REGISTRY"


def test_registry_has_required_fields():
    """Each registry entry must have provider, display_name, and credit_cost_usd."""
    for model_id, info in MODEL_REGISTRY.items():
        assert "provider" in info, f"{model_id} missing provider"
        assert "display_name" in info, f"{model_id} missing display_name"
        assert "credit_cost_usd" in info, f"{model_id} missing credit_cost_usd"
        assert info["credit_cost_usd"] > 0, f"{model_id} has non-positive cost"


def test_affordable_models_are_cheap():
    """Affordable models should cost $4 or less."""
    for model_id in FREE_TIER_MODELS:
        cost = MODEL_REGISTRY[model_id]["credit_cost_usd"]
        assert cost <= 4, f"{model_id} costs ${cost}, expected <= $4"


def test_default_models_exist():
    """Default models must be in the registry."""
    assert DEFAULT_FREE_MODEL in MODEL_REGISTRY
    assert DEFAULT_PAID_MODEL in MODEL_REGISTRY


def test_default_free_model_is_affordable():
    """Default free model must be in FREE_TIER_MODELS."""
    assert DEFAULT_FREE_MODEL in FREE_TIER_MODELS


def test_providers_are_valid():
    """All registry providers must be valid ModelProvider values."""
    for model_id, info in MODEL_REGISTRY.items():
        assert info["provider"] in list(
            ModelProvider
        ), f"{model_id} has invalid provider {info['provider']}"


def test_google_models_exist():
    """At least one Google model must be in the registry."""
    google_models = [
        m for m, r in MODEL_REGISTRY.items() if r["provider"] == ModelProvider.GOOGLE
    ]
    assert len(google_models) >= 1


def test_anthropic_models_exist():
    """At least one Anthropic model must be in the registry."""
    anthropic_models = [
        m for m, r in MODEL_REGISTRY.items() if r["provider"] == ModelProvider.CLAUDE
    ]
    assert len(anthropic_models) >= 1

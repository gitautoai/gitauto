from constants.models import MODEL_REGISTRY, ClaudeModelId, GoogleModelId
from services.get_fallback_models import (
    CLAUDE_FALLBACK_MODELS,
    GOOGLE_FALLBACK_MODELS,
    get_fallback_models,
)


def test_claude_chain_order():
    """Claude chain has newest Opus first, then fallback models."""
    assert CLAUDE_FALLBACK_MODELS == [
        ClaudeModelId.OPUS_4_7,
        ClaudeModelId.OPUS_4_6,
        ClaudeModelId.OPUS_4_5,
        ClaudeModelId.SONNET_4_6,
        ClaudeModelId.SONNET_4_5,
    ]


def test_google_chain_order():
    """Google chain has most capable first: Gemini Flash, then Gemma."""
    assert GOOGLE_FALLBACK_MODELS == [
        GoogleModelId.GEMINI_2_5_FLASH,
        GoogleModelId.GEMMA_4_31B,
    ]


def test_get_fallback_models_opus_excludes_self():
    """Opus fallbacks don't include Opus itself."""
    fallbacks = get_fallback_models(ClaudeModelId.OPUS_4_7)
    assert ClaudeModelId.OPUS_4_7 not in fallbacks
    assert fallbacks == [
        ClaudeModelId.OPUS_4_6,
        ClaudeModelId.OPUS_4_5,
        ClaudeModelId.SONNET_4_6,
        ClaudeModelId.SONNET_4_5,
    ]


def test_get_fallback_models_sonnet_46_excludes_opus():
    """Sonnet ($4) never falls back to Opus ($8)."""
    fallbacks = get_fallback_models(ClaudeModelId.SONNET_4_6)
    assert fallbacks == [ClaudeModelId.SONNET_4_5]
    assert ClaudeModelId.OPUS_4_7 not in fallbacks
    assert ClaudeModelId.OPUS_4_6 not in fallbacks
    assert ClaudeModelId.OPUS_4_5 not in fallbacks


def test_get_fallback_models_gemma_excludes_gemini():
    """Gemma ($2) can't fall back to Gemini ($4)."""
    fallbacks = get_fallback_models(GoogleModelId.GEMMA_4_31B)
    assert fallbacks == []
    assert GoogleModelId.GEMINI_2_5_FLASH not in fallbacks


def test_get_fallback_models_gemini_falls_back_to_gemma():
    """Gemini ($4) can fall back to cheaper Gemma ($2)."""
    fallbacks = get_fallback_models(GoogleModelId.GEMINI_2_5_FLASH)
    assert fallbacks == [GoogleModelId.GEMMA_4_31B]


def test_fallback_never_includes_preferred():
    """The preferred model is never in its own fallback list."""
    for preferred in [*ClaudeModelId, *GoogleModelId]:
        fallbacks = get_fallback_models(preferred)
        assert (
            preferred not in fallbacks
        ), f"Preferred model {preferred} should not be in its own fallbacks"


def test_fallback_never_more_expensive():
    """Every model in a fallback list must cost <= the preferred model."""
    for preferred in [*ClaudeModelId, *GoogleModelId]:
        fallbacks = get_fallback_models(preferred)
        preferred_cost = MODEL_REGISTRY[preferred]["credit_cost_usd"]
        for model in fallbacks:
            model_cost = MODEL_REGISTRY[model]["credit_cost_usd"]
            assert model_cost <= preferred_cost, (
                f"Fallback {model} (${model_cost}) is more expensive than "
                f"preferred {preferred} (${preferred_cost})"
            )


def test_all_chain_elements_are_model_id():
    """Every element in both chains is a ModelId."""
    for model in CLAUDE_FALLBACK_MODELS:
        assert isinstance(model, (ClaudeModelId, GoogleModelId))
    for model in GOOGLE_FALLBACK_MODELS:
        assert isinstance(model, (ClaudeModelId, GoogleModelId))


def test_no_cross_provider_fallback():
    """Google chain never contains Claude models and vice versa."""
    for model in CLAUDE_FALLBACK_MODELS:
        assert model not in GOOGLE_FALLBACK_MODELS
    for model in GOOGLE_FALLBACK_MODELS:
        assert model not in CLAUDE_FALLBACK_MODELS

from constants.models import (
    MODEL_REGISTRY,
    ClaudeModelId,
    GoogleModelId,
    ModelId,
    ModelProvider,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Full fallback chains for resilience — includes non-user-selectable models
CLAUDE_FALLBACK_MODELS: list[ModelId] = [
    ClaudeModelId.OPUS_4_7,
    ClaudeModelId.OPUS_4_6,
    ClaudeModelId.OPUS_4_5,
    ClaudeModelId.SONNET_4_6,
    ClaudeModelId.SONNET_4_5,
]

GOOGLE_FALLBACK_MODELS: list[ModelId] = [
    GoogleModelId.GEMINI_2_5_FLASH,
    GoogleModelId.GEMMA_4_31B,
]


@handle_exceptions(
    default_return_value=list(CLAUDE_FALLBACK_MODELS), raise_on_error=False
)
def get_fallback_models(preferred_model: ModelId):
    """Return the fallback chain for a given model, within the same provider."""
    entry = MODEL_REGISTRY.get(preferred_model)
    if not entry:
        logger.warning("Unknown model %s, using Claude chain", preferred_model)
        return list(CLAUDE_FALLBACK_MODELS)

    provider = entry["provider"]
    if provider == ModelProvider.GOOGLE:
        chain = list(GOOGLE_FALLBACK_MODELS)
    else:
        chain = list(CLAUDE_FALLBACK_MODELS)

    # Never fall back to a more expensive model than what the user chose
    preferred_cost = entry["credit_cost_usd"]
    chain = [m for m in chain if MODEL_REGISTRY[m]["credit_cost_usd"] <= preferred_cost]

    # Remove the preferred model itself — caller already has it
    chain = [m for m in chain if m != preferred_model]

    logger.info("Fallback models for %s: %s", preferred_model, chain)
    return chain

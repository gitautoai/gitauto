from enum import StrEnum
from typing import TypedDict


class ClaudeModelId(StrEnum):
    """Claude models — user-selectable and fallback-only."""

    OPUS_4_7 = "claude-opus-4-7"
    OPUS_4_6 = "claude-opus-4-6"
    SONNET_4_6 = "claude-sonnet-4-6"
    OPUS_4_5 = "claude-opus-4-5"
    SONNET_4_5 = "claude-sonnet-4-5"
    HAIKU_4_5 = "claude-haiku-4-5"


class GoogleModelId(StrEnum):
    """Google AI models — user-selectable."""

    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMMA_4_31B = "gemma-4-31b-it"


ModelId = ClaudeModelId | GoogleModelId


class ModelProvider(StrEnum):
    """Identifies which API to route requests to in chat_with_model."""

    CLAUDE = "claude"
    GOOGLE = "google"


class ModelInfo(TypedDict):
    """Metadata for a model: provider routing, display name, credit cost, and selectability."""

    provider: ModelProvider
    display_name: str
    credit_cost_usd: int
    user_selectable: bool
    free_tier: bool


MODEL_REGISTRY: dict[ModelId, ModelInfo] = {
    # Claude (user-selectable)
    ClaudeModelId.OPUS_4_7: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Opus 4.7",
        credit_cost_usd=8,
        user_selectable=True,
        free_tier=False,
    ),
    ClaudeModelId.SONNET_4_6: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Sonnet 4.6",
        credit_cost_usd=4,
        user_selectable=True,
        free_tier=True,
    ),
    # Claude (fallback-only, same cost as their newer versions)
    ClaudeModelId.OPUS_4_6: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Opus 4.6",
        credit_cost_usd=8,
        user_selectable=False,
        free_tier=False,
    ),
    ClaudeModelId.OPUS_4_5: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Opus 4.5",
        credit_cost_usd=8,
        user_selectable=False,
        free_tier=False,
    ),
    ClaudeModelId.SONNET_4_5: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Sonnet 4.5",
        credit_cost_usd=4,
        user_selectable=False,
        free_tier=False,
    ),
    ClaudeModelId.HAIKU_4_5: ModelInfo(
        provider=ModelProvider.CLAUDE,
        display_name="Claude Haiku 4.5",
        credit_cost_usd=2,
        user_selectable=False,
        free_tier=False,
    ),
    # Google (user-selectable)
    GoogleModelId.GEMINI_2_5_FLASH: ModelInfo(
        provider=ModelProvider.GOOGLE,
        display_name="Gemini 2.5 Flash",
        credit_cost_usd=4,
        user_selectable=True,
        free_tier=True,
    ),
    GoogleModelId.GEMMA_4_31B: ModelInfo(
        provider=ModelProvider.GOOGLE,
        display_name="Gemma 4 31B",
        credit_cost_usd=2,
        user_selectable=True,
        free_tier=True,
    ),
}

MODEL_ID_BY_VALUE: dict[str, ModelId] = {m.value: m for m in MODEL_REGISTRY}
USER_SELECTABLE_MODELS = [m for m, r in MODEL_REGISTRY.items() if r["user_selectable"]]
FREE_TIER_MODELS = [
    m for m, r in MODEL_REGISTRY.items() if r["user_selectable"] and r["free_tier"]
]
DEFAULT_FREE_MODEL = GoogleModelId.GEMMA_4_31B
DEFAULT_PAID_MODEL = ClaudeModelId.OPUS_4_7
MAX_CREDIT_COST_USD = max(entry["credit_cost_usd"] for entry in MODEL_REGISTRY.values())
CREDIT_GRANT_AMOUNT_USD = MAX_CREDIT_COST_USD * 3

import os
from enum import StrEnum

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases
class ClaudeModelId(StrEnum):
    OPUS_4_6 = "claude-opus-4-6"
    OPUS_4_5 = "claude-opus-4-5"
    SONNET_4_6 = "claude-sonnet-4-6"
    SONNET_4_5 = "claude-sonnet-4-5"
    SONNET_4_0 = "claude-sonnet-4-0"


# https://platform.claude.com/docs/en/docs/about-claude/models/all-models#model-comparison-table
CONTEXT_WINDOW: dict[ClaudeModelId, int] = {
    ClaudeModelId.OPUS_4_6: 1_000_000,
    ClaudeModelId.SONNET_4_6: 1_000_000,
    ClaudeModelId.OPUS_4_5: 200_000,
    ClaudeModelId.SONNET_4_5: 200_000,  # 1M available with context-1m-2025-08-07 beta header
    ClaudeModelId.SONNET_4_0: 200_000,  # 1M available with context-1m-2025-08-07 beta header
}

MAX_OUTPUT_TOKENS: dict[ClaudeModelId, int] = {
    ClaudeModelId.OPUS_4_6: 128_000,
    ClaudeModelId.SONNET_4_6: 64_000,
    ClaudeModelId.OPUS_4_5: 64_000,
    ClaudeModelId.SONNET_4_5: 64_000,
    ClaudeModelId.SONNET_4_0: 64_000,
}

MODEL_CHAIN = [
    ClaudeModelId.OPUS_4_6,
    ClaudeModelId.OPUS_4_5,
    ClaudeModelId.SONNET_4_6,
    ClaudeModelId.SONNET_4_5,
    ClaudeModelId.SONNET_4_0,
]

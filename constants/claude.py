import os

from constants.models import ClaudeModelId

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# https://platform.claude.com/docs/en/docs/about-claude/models/all-models#model-comparison-table
CONTEXT_WINDOW: dict[ClaudeModelId, int] = {
    ClaudeModelId.OPUS_4_7: 1_000_000,
    ClaudeModelId.OPUS_4_6: 1_000_000,
    ClaudeModelId.SONNET_4_6: 1_000_000,
    ClaudeModelId.OPUS_4_5: 200_000,
    ClaudeModelId.SONNET_4_5: 200_000,
    ClaudeModelId.HAIKU_4_5: 200_000,
}

MAX_OUTPUT_TOKENS: dict[ClaudeModelId, int] = {
    ClaudeModelId.OPUS_4_7: 128_000,
    ClaudeModelId.OPUS_4_6: 128_000,
    ClaudeModelId.SONNET_4_6: 64_000,
    ClaudeModelId.OPUS_4_5: 64_000,
    ClaudeModelId.SONNET_4_5: 64_000,
    ClaudeModelId.HAIKU_4_5: 64_000,
}

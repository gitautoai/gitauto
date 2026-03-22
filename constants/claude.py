from enum import StrEnum

from utils.env import get_env_var

CLAUDE_API_KEY = get_env_var(name="ANTHROPIC_API_KEY")


# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases
class ClaudeModelId(StrEnum):
    OPUS_4_6 = "claude-opus-4-6"
    OPUS_4_5 = "claude-opus-4-5"
    SONNET_4_6 = "claude-sonnet-4-6"
    SONNET_4_5 = "claude-sonnet-4-5"
    SONNET_4_0 = "claude-sonnet-4-0"


CLAUDE_MAX_TOKENS = 64000

MODEL_CHAIN = [
    ClaudeModelId.OPUS_4_6,
    ClaudeModelId.OPUS_4_5,
    ClaudeModelId.SONNET_4_6,
    ClaudeModelId.SONNET_4_5,
    ClaudeModelId.SONNET_4_0,
]

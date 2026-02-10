from utils.env import get_env_var

CLAUDE_API_KEY = get_env_var(name="ANTHROPIC_API_KEY")

# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases
CLAUDE_OPUS_4_6 = "claude-opus-4-6"
CLAUDE_MODEL_ID_45 = "claude-sonnet-4-5"
CLAUDE_MODEL_ID_40 = "claude-sonnet-4-0"
CLAUDE_MODEL_ID_37 = "claude-3-7-sonnet-latest"

CLAUDE_MAX_TOKENS = 64000

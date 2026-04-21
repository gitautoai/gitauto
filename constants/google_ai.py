import os

from constants.models import GoogleModelId

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")


# https://ai.google.dev/gemini-api/docs/models
CONTEXT_WINDOW: dict[GoogleModelId, int] = {
    GoogleModelId.GEMINI_2_5_FLASH: 1_048_576,
    GoogleModelId.GEMMA_4_31B: 262_144,
}

MAX_OUTPUT_TOKENS: dict[GoogleModelId, int] = {
    GoogleModelId.GEMINI_2_5_FLASH: 65_536,
    GoogleModelId.GEMMA_4_31B: 8_192,
}

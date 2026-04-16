import json

from google.genai import types

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import (
    ClaudeModelId,
    GoogleModelId,
    MODEL_REGISTRY,
    ModelId,
    ModelProvider,
)
from services.claude.client import claude
from services.google_ai.client import get_google_ai_client
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.prompts.quality_check import QUALITY_CHECK_SYSTEM_PROMPT

SYSTEM = (
    QUALITY_CHECK_SYSTEM_PROMPT
    + "\n\nRespond with ONLY the JSON object, no other text."
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def evaluate_quality_checks(
    source_content: str,
    source_path: str,
    test_files: list[tuple[str, str]],
    model: ModelId,
):
    """test_files: list of (path, content) tuples for all test files covering this source."""
    if not source_content:
        logger.info("Empty source content for %s", source_path)
        return None

    user_message = f"## Source file: {source_path}\n\n```\n{source_content}\n```"
    if test_files:
        for path, content in test_files:
            user_message += f"\n\n## Test file: {path}\n\n```\n{content}\n```"
    else:
        user_message += "\n\n## Test file: No test file exists for this source file."

    provider = MODEL_REGISTRY[model]["provider"]
    if provider == ModelProvider.CLAUDE:
        assert isinstance(model, ClaudeModelId)
        response = claude.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS[model],
            temperature=0,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        text_attr = getattr(response.content[0], "text", "")
        if not isinstance(text_attr, str):
            logger.error("Expected str but got %s: %s", type(text_attr), text_attr)
            return None
        text = text_attr
    elif provider == ModelProvider.GOOGLE:
        assert isinstance(model, GoogleModelId)
        client = get_google_ai_client()
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM,
            temperature=0.0,
        )
        response = client.models.generate_content(
            model=model,
            contents=user_message,
            config=config,
        )
        text = response.text or ""
    else:
        logger.error("Unknown provider %s for model %s", provider, model)
        return None

    if not text:
        logger.info("Empty response from model for quality checks on %s", source_path)
        return None

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    result: dict[str, dict[str, dict[str, str]]] = json.loads(text)
    logger.info(
        "Quality checks for %s: %s categories evaluated", source_path, len(result)
    )
    return result

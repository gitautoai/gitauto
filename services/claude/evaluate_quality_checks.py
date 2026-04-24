import json
import time

from anthropic.types import MessageParam
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
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
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
    usage_id: int,
    created_by: str,
):
    """test_files: list of (path, content) tuples for all test files covering this source."""
    if not source_content:
        logger.info("Empty source content for %s", source_path)
        return None

    user_message = f"## Source file: {source_path}\n\n```\n{source_content}\n```"
    if test_files:
        logger.info("evaluate_quality_checks: appending %d test files", len(test_files))
        for path, content in test_files:
            user_message += f"\n\n## Test file: {path}\n\n```\n{content}\n```"
    else:
        logger.info("evaluate_quality_checks: no test files for %s", source_path)
        user_message += "\n\n## Test file: No test file exists for this source file."

    provider = MODEL_REGISTRY[model]["provider"]
    user_msg: MessageParam = {"role": "user", "content": user_message}
    if provider == ModelProvider.CLAUDE:
        logger.info("evaluate_quality_checks: using Claude provider with %s", model)
        assert isinstance(model, ClaudeModelId)
        # Opus 4.7 deprecated the temperature parameter; omit it to stay compatible across models.
        start = time.time()
        response = claude.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS[model],
            system=SYSTEM,
            messages=[user_msg],
        )
        response_time_ms = int((time.time() - start) * 1000)
        text_attr = getattr(response.content[0], "text", "")
        if not isinstance(text_attr, str):
            logger.error("Expected str but got %s: %s", type(text_attr), text_attr)
            text = ""
        else:
            logger.info(
                "evaluate_quality_checks: Claude text received (%d chars)",
                len(text_attr),
            )
            text = text_attr
        insert_llm_request(
            usage_id=usage_id,
            provider="claude",
            model_id=model,
            input_messages=[user_msg],
            input_tokens=response.usage.input_tokens if response.usage else 0,
            output_message={"role": "assistant", "content": text},
            output_tokens=response.usage.output_tokens if response.usage else 0,
            system_prompt=SYSTEM,
            response_time_ms=response_time_ms,
            created_by=created_by,
        )
        if not text:
            logger.info(
                "evaluate_quality_checks: returning None for invalid Claude response"
            )
            return None
    elif provider == ModelProvider.GOOGLE:
        logger.info("evaluate_quality_checks: using Google provider with %s", model)
        assert isinstance(model, GoogleModelId)
        client = get_google_ai_client()
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM,
            temperature=0.0,
        )
        start = time.time()
        response = client.models.generate_content(
            model=model,
            contents=user_message,
            config=config,
        )
        response_time_ms = int((time.time() - start) * 1000)
        text = response.text or ""
        usage = response.usage_metadata
        insert_llm_request(
            usage_id=usage_id,
            provider="google",
            model_id=model,
            input_messages=[user_msg],
            input_tokens=(usage.prompt_token_count or 0) if usage else 0,
            output_message={"role": "assistant", "content": text},
            output_tokens=(usage.candidates_token_count or 0) if usage else 0,
            system_prompt=SYSTEM,
            response_time_ms=response_time_ms,
            created_by=created_by,
        )
    else:
        logger.error("Unknown provider %s for model %s", provider, model)
        return None

    if not text:
        logger.info("Empty response from model for quality checks on %s", source_path)
        return None

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        logger.info("evaluate_quality_checks: stripping markdown code fence")
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            logger.info("evaluate_quality_checks: stripping trailing fence")
            text = text[:-3].strip()

    result: dict[str, dict[str, dict[str, str]]] = json.loads(text)
    logger.info(
        "Quality checks for %s: %s categories evaluated", source_path, len(result)
    )
    return result

import json
import time
from dataclasses import dataclass
from typing import Literal, TypedDict

from anthropic.types import MessageParam

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId
from services.claude.client import claude
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


class OutputFormat(TypedDict):
    type: Literal["json_schema"]
    schema: dict[str, object]


@dataclass
class EvaluationResult:
    result: bool
    reason: str


RESPONSE_SCHEMA: OutputFormat = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "result": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["result", "reason"],
        "additionalProperties": False,
    },
}


@handle_exceptions(
    default_return_value=EvaluationResult(False, "evaluation failed"),
    raise_on_error=False,
)
def evaluate_condition(
    content: str,
    system_prompt: str,
    usage_id: int,
    created_by: str,
):
    if not content or not system_prompt:
        logger.info("evaluate_condition skipped: empty content or system_prompt")
        return EvaluationResult(False, "empty input")

    model_id = ClaudeModelId.OPUS_4_7
    user_msg: MessageParam = {"role": "user", "content": content}

    # Opus 4.7 deprecated the temperature parameter; passing it raises 400.
    start = time.time()
    response = claude.messages.create(
        model=model_id,
        max_tokens=MAX_OUTPUT_TOKENS[model_id],
        system=system_prompt,
        messages=[user_msg],
        output_config={"format": RESPONSE_SCHEMA},
    )
    response_time_ms = int((time.time() - start) * 1000)

    text_attr = getattr(response.content[0], "text", "")
    if not isinstance(text_attr, str):
        logger.error("Expected str but got %s: %s", type(text_attr), text_attr)
        output_message: MessageParam = {"role": "assistant", "content": ""}
    else:
        logger.info(
            "evaluate_condition: received text response (%d chars)", len(text_attr)
        )
        output_message = {"role": "assistant", "content": text_attr}

    insert_llm_request(
        usage_id=usage_id,
        provider="claude",
        model_id=model_id,
        input_messages=[user_msg],
        input_tokens=response.usage.input_tokens if response.usage else 0,
        output_message=output_message,
        output_tokens=response.usage.output_tokens if response.usage else 0,
        system_prompt=system_prompt,
        response_time_ms=response_time_ms,
        created_by=created_by,
    )

    if not isinstance(text_attr, str):
        logger.info("evaluate_condition returning invalid-format fallback")
        return EvaluationResult(False, "invalid response format")

    logger.info("evaluate_condition returning parsed result")
    return EvaluationResult(**json.loads(text_attr.strip()))

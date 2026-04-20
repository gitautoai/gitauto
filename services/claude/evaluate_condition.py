import json
from dataclasses import dataclass
from typing import Literal, TypedDict

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId
from services.claude.client import claude
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
):
    if not content or not system_prompt:
        logger.info("evaluate_condition skipped: empty content or system_prompt")
        return EvaluationResult(False, "empty input")

    # Opus 4.7 deprecated the temperature parameter; passing it raises 400.
    response = claude.beta.messages.create(
        model=ClaudeModelId.OPUS_4_7,
        max_tokens=MAX_OUTPUT_TOKENS[ClaudeModelId.OPUS_4_7],
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
        betas=["structured-outputs-2025-11-13"],
        output_config={"format": RESPONSE_SCHEMA},
    )

    text_attr = getattr(response.content[0], "text", "")
    if not isinstance(text_attr, str):
        logger.error("Expected str but got %s: %s", type(text_attr), text_attr)
        return EvaluationResult(False, "invalid response format")

    logger.info("evaluate_condition returning parsed result")
    return EvaluationResult(**json.loads(text_attr.strip()))

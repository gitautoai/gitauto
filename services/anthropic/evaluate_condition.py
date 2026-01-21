import json
from typing import Literal, TypedDict

from config import ANTHROPIC_MODEL_ID_45
from services.anthropic.client import claude
from utils.error.handle_exceptions import handle_exceptions


class OutputFormat(TypedDict):
    type: Literal["json_schema"]
    schema: dict[str, object]


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
    default_return_value=(False, "evaluation failed"), raise_on_error=False
)
def evaluate_condition(
    content: str,
    system_prompt: str,
    max_tokens: int = 100,
):
    if not content or not system_prompt:
        return (False, "empty input")

    response = claude.beta.messages.create(
        model=ANTHROPIC_MODEL_ID_45,
        max_tokens=max_tokens,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
        betas=["structured-outputs-2025-11-13"],
        output_format=RESPONSE_SCHEMA,
    )

    response_text = getattr(response.content[0], "text", "").strip()
    data = json.loads(response_text)
    return (data["result"], data["reason"])

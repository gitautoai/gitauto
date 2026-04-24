import json
import time
from dataclasses import dataclass
from typing import Literal

from anthropic.types import MessageParam

from constants.claude import MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId
from services.claude.client import claude
from services.claude.evaluate_condition import OutputFormat
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.logging.logging_config import logger

SYSTEM_PROMPT = """You are a code analysis expert. Determine if the given uncovered code is DEAD CODE (should be removed) or GENUINELY UNTESTABLE (needs coverage exclusion).

Return true if the code falls into EITHER category:

DEAD CODE (must be REMOVED, not excluded from coverage):
1. Logically unreachable code due to earlier conditions already handling the case (e.g., checking `x === ''` after `!x` already returned, since empty string is falsy)
2. Code after unconditional return/throw/break statements
3. Branches that can never execute given the type system or prior logic

GENUINELY UNTESTABLE (may use coverage exclusion as last resort):
1. Async error handlers in React/Vue/Angular event handlers (onClick, onSubmit) that throw errors - become unhandled promise rejections
2. Error throws inside callbacks that test frameworks cannot catch
3. Code paths only executing in specific runtime environments tests cannot simulate
4. Race condition handlers depending on timing

Code is TESTABLE (return false) if:
1. Can be tested by mocking dependencies
2. Can be tested by spying on console.error/console.log
3. Can be tested by checking UI state changes
4. Simply missing test coverage but technically testable

Return:
- result: true if dead code OR genuinely untestable, false if testable
- category: "dead_code" if unreachable/redundant, "untestable" if genuinely untestable, "testable" if testable
- reason: which line numbers are affected and why
"""

RESPONSE_SCHEMA: OutputFormat = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "result": {"type": "boolean"},
            "category": {
                "type": "string",
                "enum": ["dead_code", "untestable", "testable"],
            },
            "reason": {"type": "string"},
        },
        "required": ["result", "category", "reason"],
        "additionalProperties": False,
    },
}


@dataclass
class CodeAnalysisResult:
    result: bool
    category: Literal["dead_code", "untestable", "testable"]
    reason: str


@handle_exceptions(
    default_return_value=None,
    raise_on_error=False,
)
def is_code_untestable(
    file_path: str,
    file_content: str,
    usage_id: int,
    created_by: str,
    uncovered_lines: str | None = None,
    uncovered_functions: str | None = None,
    uncovered_branches: str | None = None,
):
    parts: list[str] = []

    # Extract uncovered lines from file content
    if uncovered_lines:
        logger.info(
            "is_code_untestable: extracting uncovered_lines=%s", uncovered_lines
        )
        line_nums = [int(n.strip()) for n in uncovered_lines.split(",") if n.strip()]
        lines = file_content.splitlines()
        extracted: list[str] = []
        for num in line_nums:
            if 0 < num <= len(lines):
                logger.info("is_code_untestable: keeping line %d", num)
                extracted.append(f"{num}: {lines[num - 1]}")
        if extracted:
            logger.info(
                "is_code_untestable: adding %d extracted lines to parts", len(extracted)
            )
            parts.append(f"Uncovered lines:\n```\n{"\n".join(extracted)}\n```")

    if uncovered_functions:
        logger.info(
            "is_code_untestable: adding uncovered_functions=%s", uncovered_functions
        )
        parts.append(f"Uncovered functions: {uncovered_functions}")

    if uncovered_branches:
        logger.info(
            "is_code_untestable: adding uncovered_branches=%s", uncovered_branches
        )
        parts.append(f"Uncovered branches: {uncovered_branches}")

    if not parts:
        logger.info(
            "is_code_untestable: no uncovered code provided, returning testable"
        )
        return CodeAnalysisResult(False, "testable", "No uncovered code provided")

    numbered_file = format_content_with_line_numbers(
        file_path=file_path, content=file_content
    )

    content = f"""{"\n".join(parts)}

{numbered_file}

Is this code dead (unreachable/redundant) or genuinely untestable (reachable at runtime but impossible to test)?"""

    model_id = ClaudeModelId.OPUS_4_7
    user_msg: MessageParam = {"role": "user", "content": content}

    # Opus 4.7 deprecated the temperature parameter; passing it raises 400.
    start = time.time()
    response = claude.messages.create(
        model=model_id,
        max_tokens=MAX_OUTPUT_TOKENS[model_id],
        system=SYSTEM_PROMPT,
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
            "is_code_untestable: received text response (%d chars)", len(text_attr)
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
        system_prompt=SYSTEM_PROMPT,
        response_time_ms=response_time_ms,
        created_by=created_by,
    )

    if not isinstance(text_attr, str):
        logger.info("is_code_untestable returning None due to invalid response format")
        return None

    logger.info("is_code_untestable returning parsed result")
    return CodeAnalysisResult(**json.loads(text_attr.strip()))

import json
from typing import Sequence

from anthropic.types import MessageParam
from openai.types.chat import ChatCompletionMessageParam

from schemas.supabase.types import LlmRequests
from services.supabase.client import supabase
from services.supabase.llm_requests.calculate_costs import calculate_costs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Both Anthropic's MessageParam and OpenAI's ChatCompletionMessageParam are TypedDicts with different role/content shapes. The union keeps per-provider typing at call sites; json.dumps handles serialization uniformly below.
LlmMessage = MessageParam | ChatCompletionMessageParam


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_llm_request(
    usage_id: int,
    provider: str,
    model_id: str,
    input_messages: Sequence[LlmMessage],
    input_tokens: int,
    output_message: LlmMessage,
    output_tokens: int,
    created_by: str,
    system_prompt: str | None = None,
    response_time_ms: int | None = None,
    error_message: str | None = None,
):
    # Claude/Google take the system prompt as a separate kwarg rather than a message, and anthropic.MessageParam's role field is Literal["user", "assistant"] (no "system"). Prepending a role="system" entry here keeps the stored JSON honest about what the model received without forcing callers to contort it into a fake user message.
    serialized_input: list[object] = []
    if system_prompt is not None:
        logger.debug(
            "insert_llm_request: prepending system prompt (%d chars)",
            len(system_prompt),
        )
        serialized_input.append({"role": "system", "content": system_prompt})
    serialized_input.extend(input_messages)
    input_content = json.dumps(serialized_input, ensure_ascii=False)
    output_content = json.dumps(output_message, ensure_ascii=False)

    # Calculate lengths
    input_length = len(input_content)
    output_length = len(output_content)

    # Calculate costs based on provider and model
    input_cost_usd, output_cost_usd = calculate_costs(
        provider, model_id, input_tokens, output_tokens
    )
    total_cost_usd = input_cost_usd + output_cost_usd

    # Insert record
    data = {
        "usage_id": usage_id,
        "provider": provider,
        "model_id": model_id,
        "input_content": input_content,
        "input_length": input_length,
        "input_tokens": input_tokens,
        "input_cost_usd": input_cost_usd,
        "output_content": output_content,
        "output_length": output_length,
        "output_tokens": output_tokens,
        "output_cost_usd": output_cost_usd,
        "total_cost_usd": total_cost_usd,
        "response_time_ms": response_time_ms,
        "error_message": error_message,
        "created_by": created_by,
        "updated_by": created_by,
    }

    result = supabase.table("llm_requests").insert(data).execute()
    if result.data:
        logger.info(
            "insert_llm_request: recorded provider=%s model=%s usage_id=%s tokens_in=%d tokens_out=%d cost_usd=%.6f",
            provider,
            model_id,
            usage_id,
            input_tokens,
            output_tokens,
            total_cost_usd,
        )
        return LlmRequests(**result.data[0])

    logger.warning(
        "insert_llm_request: insert returned no rows provider=%s model=%s usage_id=%s",
        provider,
        model_id,
        usage_id,
    )
    return None

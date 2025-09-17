import json
from typing import Any

from services.supabase.client import supabase
from services.supabase.llm_requests.calculate_costs import calculate_costs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_llm_request(
    usage_id: int,
    provider: str,
    model_id: str,
    input_messages: list[dict[str, Any]],
    input_tokens: int,
    output_message: dict[str, Any],
    output_tokens: int,
    response_time_ms: int | None = None,
    error_message: str | None = None,
    created_by: str | None = None,
):
    # Convert messages to JSON strings
    input_content = json.dumps(input_messages, ensure_ascii=False)
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
    return result.data[0] if result.data else None

import time

from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock

from constants.claude import CONTEXT_WINDOW, MAX_OUTPUT_TOKENS
from constants.models import ClaudeModelId
from services.claude.client import claude
from services.claude.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)
from services.claude.trim_messages import trim_messages_to_token_limit
from services.llm_result import LlmResult, ToolCall
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[MessageParam],
    system_content: str,
    tools: list[ToolUnionParam],
    model_id: ClaudeModelId,
    usage_id: int,
    created_by: str,
):
    # Check token count and delete messages if necessary
    buffer = 4096
    context_window = CONTEXT_WINDOW.get(model_id, 200_000)
    max_output = MAX_OUTPUT_TOKENS.get(model_id, 64_000)
    max_input = min(context_window - max_output - buffer, 200_000)
    messages, token_input = trim_messages_to_token_limit(
        messages=messages, client=claude, model=model_id, max_input=max_input
    )

    # https://docs.anthropic.com/en/api/messages
    start_time = time.time()
    try:
        response = claude.messages.create(
            model=model_id,
            system=system_content,
            messages=messages,
            tools=tools,
            # https://platform.claude.com/docs/en/docs/about-claude/models/all-models#model-comparison-table
            max_tokens=max_output,
            temperature=0.0,
        )
        response_time_ms = int((time.time() - start_time) * 1000)
    except OverloadedError as e:
        raise ClaudeOverloadedError("Claude API is overloaded (529)") from e
    except AuthenticationError as e:
        raise ClaudeAuthenticationError("Claude API authentication failed (401)") from e

    # Process the response
    content_text = ""
    tool_use_blocks: list[ToolUseBlock] = []

    for content_block in response.content:
        if content_block.type == "text":
            content_text += content_block.text
        elif content_block.type == "tool_use":
            tool_use_blocks.append(content_block)

    # Build content list with ALL content blocks
    content_list = []

    if content_text:
        content_list.append({"type": "text", "text": content_text})

    # Include ALL tool_use blocks in the assistant message
    tool_calls: list[ToolCall] = []
    for tool_use in tool_use_blocks:
        content_list.append(
            {
                "type": "tool_use",
                "id": tool_use.id,  # e.g. "toolu_01M3mtjuKhyQptQh5ASmQCFY"
                "name": tool_use.name,  # e.g. "apply_diff_to_file"
                "input": tool_use.input,
            }
        )
        tool_calls.append(
            ToolCall(id=tool_use.id, name=tool_use.name, args=tool_use.input)
        )

    # Return Claude's native format
    assistant_message: MessageParam = {
        "role": "assistant",
        "content": content_list,
    }

    # Get actual output tokens from response
    token_output = (
        response.usage.output_tokens
        if hasattr(response, "usage") and response.usage
        else 0
    )

    # Combine system message with user messages for logging
    system_msg: MessageParam = {"role": "user", "content": system_content}
    full_messages = [system_msg, *messages]
    llm_record = insert_llm_request(
        usage_id=usage_id,
        provider="claude",
        model_id=model_id,
        input_messages=full_messages,
        input_tokens=token_input,
        output_message=assistant_message,
        output_tokens=token_output,
        response_time_ms=response_time_ms,
        created_by=created_by,
    )
    cost_usd = llm_record["total_cost_usd"] if llm_record else 0.0

    return LlmResult(
        assistant_message=assistant_message,
        tool_calls=tool_calls,
        token_input=token_input,
        token_output=token_output,
        cost_usd=cost_usd,
    )

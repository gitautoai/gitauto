# Standard imports
import time
from typing import Any, cast

# Third party imports
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock
from openai.types.chat import ChatCompletionToolParam

# Local imports
from config import ANTHROPIC_MODEL_ID_45
from services.anthropic.client import claude
from services.anthropic.remove_duplicate_get_remote_file_content_results import (
    remove_duplicate_get_remote_file_content_results,
)
from services.anthropic.remove_get_remote_file_content_before_replace_remote_file_content import (
    remove_get_remote_file_content_before_replace_remote_file_content,
)
from services.anthropic.remove_outdated_apply_diff_to_file_attempts_and_results import (
    remove_outdated_apply_diff_to_file_attempts_and_results,
)
from services.anthropic.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)
from services.anthropic.message_to_dict import message_to_dict
from services.anthropic.trim_messages import trim_messages_to_token_limit
from services.supabase.llm_requests.insert_llm_request import insert_llm_request
from utils.error.handle_exceptions import handle_exceptions
from utils.objects.safe_get_attribute import safe_get_attribute


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[dict[str, Any]],
    system_content: str,
    tools: list[ChatCompletionToolParam],
    model_id: str = ANTHROPIC_MODEL_ID_45,
    usage_id: int | None = None,
):
    # https://docs.anthropic.com/en/api/client-sdks
    # Apply all message deduplication functions to save tokens
    messages = remove_duplicate_get_remote_file_content_results(messages)
    messages = remove_get_remote_file_content_before_replace_remote_file_content(
        messages
    )
    messages = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Check token count and delete messages if necessary
    max_tokens = 64000
    buffer = 4096
    max_input = 200_000 - max_tokens - buffer
    messages = trim_messages_to_token_limit(
        messages=messages, client=claude, model=model_id, max_input=max_input
    )

    # Convert OpenAI tools format to Anthropic tools format
    anthropic_tools: list[ToolUnionParam] = []
    for tool in tools:
        tool_dict = message_to_dict(tool)
        function = safe_get_attribute(tool_dict, "function", {})
        if not isinstance(function, dict):
            function = message_to_dict(function)

        name = safe_get_attribute(function, "name", "")
        description = safe_get_attribute(function, "description", "")
        input_schema = safe_get_attribute(function, "parameters", {})

        if name and description:
            anthropic_tools.append(
                cast(
                    ToolUnionParam,
                    {
                        "name": name,
                        "description": description,
                        "input_schema": input_schema,
                    },
                )
            )

    # https://docs.anthropic.com/en/api/messages
    start_time = time.time()
    try:
        response = claude.messages.create(
            model=model_id,
            system=system_content,
            messages=cast(list[MessageParam], messages),
            tools=anthropic_tools,
            # https://docs.anthropic.com/en/docs/about-claude/models/all-models#model-comparison-table
            max_tokens=max_tokens,
            temperature=0.0,
        )
        response_time_ms = int((time.time() - start_time) * 1000)
    except OverloadedError as e:
        raise ClaudeOverloadedError("Claude API is overloaded (529)") from e
    except AuthenticationError as e:
        raise ClaudeAuthenticationError("Claude API authentication failed (401)") from e

    # Calculate tokens
    token_input = claude.messages.count_tokens(
        messages=cast(list[MessageParam], messages), model=model_id
    ).input_tokens

    # Process the response
    tool_call_id = None
    tool_name = None
    tool_args = None
    content_text = ""

    # Check for tool calls in the response
    tool_use_blocks = []

    for content_block in response.content:
        if content_block.type == "text":
            content_text += content_block.text
        elif content_block.type == "tool_use":
            tool_use_blocks.append(content_block)

    # Return Claude's native format
    assistant_message = {
        "role": "assistant",
        "content": [],
    }

    if content_text:  # Only add text block if there's content
        assistant_message["content"].append({"type": "text", "text": content_text})

    if tool_use_blocks:
        # Process the first tool call
        tool_use: ToolUseBlock = tool_use_blocks[0]
        tool_call_id = tool_use.id  # e.g. "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        tool_name = tool_use.name  # e.g. "apply_diff_to_file"
        tool_args = tool_use.input

        assistant_message["content"].append(
            {
                "type": "tool_use",
                "id": tool_call_id,
                "name": tool_name,
                "input": tool_args,
            }
        )

    # Get actual output tokens from response
    token_output = (
        response.usage.output_tokens
        if hasattr(response, "usage") and response.usage
        else 0
    )

    # Combine system message with user messages for logging
    if usage_id is not None:
        full_messages = [{"role": "system", "content": system_content}] + messages
        insert_llm_request(
            usage_id=usage_id,
            provider="claude",
            model_id=model_id,
            input_messages=full_messages,
            input_tokens=token_input,
            output_message=assistant_message,
            output_tokens=token_output,
            response_time_ms=response_time_ms,
        )

    return (
        assistant_message,
        tool_call_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )

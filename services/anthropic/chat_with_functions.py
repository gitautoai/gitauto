# Standard imports
from typing import Any

# Third party imports
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock

# Local imports
from config import ANTHROPIC_MODEL_ID_37, ANTHROPIC_MODEL_ID_40
from services.anthropic.client import claude
from services.anthropic.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)
from services.anthropic.message_to_dict import message_to_dict
from services.anthropic.trim_messages import trim_messages_to_token_limit
from utils.error.handle_exceptions import handle_exceptions
from utils.objects.safe_get_attribute import safe_get_attribute


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[MessageParam],
    system_content: str,
    tools: list[dict[str, Any]],
    model_id: str = ANTHROPIC_MODEL_ID_40,
):
    # https://docs.anthropic.com/en/api/client-sdks
    # Check token count and delete messages if necessary
    max_tokens = (
        64000 if model_id in [ANTHROPIC_MODEL_ID_37, ANTHROPIC_MODEL_ID_40] else 8192
    )
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
                {
                    "name": name,
                    "description": description,
                    "input_schema": input_schema,
                }
            )

    # https://docs.anthropic.com/en/api/messages
    try:
        response = claude.messages.create(
            model=model_id,
            system=system_content,
            messages=messages,
            tools=anthropic_tools,
            # https://docs.anthropic.com/en/docs/about-claude/models/all-models#model-comparison-table
            max_tokens=max_tokens,
            temperature=0.0,
        )
    except OverloadedError as e:
        raise ClaudeOverloadedError("Claude API is overloaded (529)") from e
    except AuthenticationError as e:
        raise ClaudeAuthenticationError("Claude API authentication failed (401)") from e

    # Calculate tokens (approximation using OpenAI's tokenizer)
    # Convert messages to dicts for token counting
    token_input = claude.messages.count_tokens(
        messages=messages, model=model_id
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

    token_output = 0
    # token_output = claude.messages.count_tokens(
    #     messages=[assistant_message], model=model_id
    # )

    return (
        assistant_message,
        tool_call_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )

# Standard imports
import json
from typing import Any

# Third party imports
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock

# Local imports
from config import ANTHROPIC_MODEL_ID_37, TIMEOUT
from services.anthropic.client import get_anthropic_client
from services.anthropic.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)
from services.anthropic.message_to_dict import message_to_dict
from services.anthropic.trim_messages import trim_messages_to_token_limit
from services.openai.count_tokens import count_tokens
from utils.attribute.safe_get_attribute import safe_get_attribute
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[MessageParam],
    system_content: str,
    tools: list[dict[str, Any]],
    model_id: str = ANTHROPIC_MODEL_ID_37,
):
    # https://docs.anthropic.com/en/api/client-sdks
    client = get_anthropic_client()

    # Check token count and delete messages if necessary
    messages = trim_messages_to_token_limit(
        messages=messages, client=client, model=model_id
    )

    # Convert OpenAI tools format to Anthropic tools format
    anthropic_tools: list[ToolUnionParam] = []
    for tool in tools:
        tool_dict = message_to_dict(tool)
        function = safe_get_attribute(tool_dict, "function", {})
        if not isinstance(function, dict):
            function = message_to_dict(function)

        anthropic_tools.append(
            {
                "name": safe_get_attribute(function, "name"),
                "description": safe_get_attribute(function, "description"),
                "input_schema": safe_get_attribute(function, "parameters"),
            }
        )

    # Call the API
    # https://docs.anthropic.com/en/api/messages
    try:
        response = client.messages.create(
            model=model_id,
            system=system_content,
            messages=messages,
            tools=anthropic_tools,
            # https://docs.anthropic.com/en/docs/about-claude/models/all-models#model-comparison-table
            max_tokens=64000 if model_id == ANTHROPIC_MODEL_ID_37 else 8192,
            temperature=0.0,
            timeout=TIMEOUT,
        )
    except OverloadedError as e:
        raise ClaudeOverloadedError("Claude API is overloaded (529)") from e
    except AuthenticationError as e:
        raise ClaudeAuthenticationError("Claude API authentication failed (401)") from e

    # Calculate tokens (approximation using OpenAI's tokenizer)
    # Convert messages to dicts for token counting
    messages_for_token_count = [message_to_dict(msg) for msg in messages]
    token_input = count_tokens(messages=messages_for_token_count)
    token_output = count_tokens(
        messages=[{"role": "assistant", "content": str(response.content)}]
    )

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

    if tool_use_blocks:
        # Process the first tool call
        tool_use: ToolUseBlock = tool_use_blocks[0]
        tool_call_id = tool_use.id  # e.g. "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        tool_name = tool_use.name  # e.g. "commit_changes_to_remote_branch"
        tool_args = tool_use.input

    # Convert Anthropic response to OpenAI format for consistency
    assistant_message = {
        "role": "assistant",
        "content": content_text,
    }

    if tool_call_id:
        assistant_message["tool_calls"] = [
            {
                "id": tool_call_id,
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(tool_args),
                },
                "type": "function",
            }
        ]

    return (
        assistant_message,
        tool_call_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )

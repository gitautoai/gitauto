# Standard imports
import json
from typing import Any

# Third party imports
from anthropic import Anthropic, AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock

# Local imports
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_ID_37, TIMEOUT
from services.openai.count_tokens import count_tokens
from utils.error.handle_exceptions import handle_exceptions


# Add this class at the top of the file
class ClaudeOverloadedError(Exception):
    """Raised when Claude API returns 529 Overloaded error"""


class ClaudeAuthenticationError(Exception):
    """Raised when Claude API returns 401 Authentication error"""


def safe_get_attribute(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get an attribute from an object or dictionary."""
    if hasattr(obj, "get") and callable(obj.get):
        # Dictionary-like object
        return obj.get(attr, default)
    elif hasattr(obj, attr):
        # Object with attributes
        return getattr(obj, attr, default)
    return default


def message_to_dict(message: Any) -> dict[str, Any]:
    """Convert a message object to a dictionary."""
    if isinstance(message, dict):
        return message

    result = {}
    for attr in ["role", "content", "tool_calls", "tool_call_id", "name"]:
        value = safe_get_attribute(message, attr)
        if value is not None:
            result[attr] = value
    return result


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[Any],
    system_content: str,
    tools: list[dict[str, Any]],
    model_id: str = ANTHROPIC_MODEL_ID_37,
):
    # https://docs.anthropic.com/en/api/client-sdks
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Convert OpenAI message format to Anthropic format
    anthropic_messages: list[MessageParam] = []
    for msg in messages:
        # Convert message to dictionary if it's an object
        msg_dict = message_to_dict(msg)

        role = safe_get_attribute(msg_dict, "role")
        content = safe_get_attribute(msg_dict, "content", "")

        if role == "user":
            anthropic_messages.append({"role": "user", "content": content})
        elif role == "assistant":
            # Handle tool calls if present
            if safe_get_attribute(msg_dict, "tool_calls"):
                tool_calls = safe_get_attribute(msg_dict, "tool_calls")
                message_content = content if content else ""
                tool_use_blocks = []

                for tool_call in tool_calls:
                    # Convert tool_call to dict if needed
                    tool_call_dict = message_to_dict(tool_call)

                    # Access function data safely
                    function = safe_get_attribute(tool_call_dict, "function", {})
                    if not isinstance(function, dict):
                        function = message_to_dict(function)

                    tool_use_blocks.append(
                        {
                            "type": "tool_use",
                            "id": safe_get_attribute(tool_call_dict, "id"),
                            "name": safe_get_attribute(function, "name"),
                            "input": json.loads(
                                safe_get_attribute(function, "arguments", "{}")
                            ),
                        }
                    )

                # Only include text block if message_content is not empty
                content_blocks = []
                if message_content:
                    content_blocks.append({"type": "text", "text": message_content})

                anthropic_messages.append(
                    {
                        "role": "assistant",
                        "content": content_blocks + tool_use_blocks,
                    }
                )
            else:
                anthropic_messages.append({"role": "assistant", "content": content})
        elif role == "tool":
            anthropic_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": safe_get_attribute(msg_dict, "tool_call_id"),
                            "content": safe_get_attribute(msg_dict, "content"),
                        }
                    ],
                }
            )
        elif role == "system":
            # System message is handled by `system` parameter
            pass

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
            messages=anthropic_messages,
            tools=anthropic_tools,
            max_tokens=8192,  # https://docs.anthropic.com/en/docs/about-claude/models/all-models
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

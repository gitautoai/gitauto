# Standard imports
import json
from typing import Any

# Local imports
from anthropic import Anthropic
from anthropic.types import MessageParam, ToolUnionParam, ToolUseBlock
from config import ANTHROPIC_MODEL_ID_35, ANTHROPIC_API_KEY, TIMEOUT
from services.openai.count_tokens import count_tokens
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_claude(
    messages: list[dict[str, Any]],
    system_content: str,
    tools: list[dict[str, Any]],
    model_id: str = ANTHROPIC_MODEL_ID_35,
):
    # https://docs.anthropic.com/en/api/client-sdks
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Convert OpenAI message format to Anthropic format
    anthropic_messages: list[MessageParam] = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")

        if role == "user":
            anthropic_messages.append({"role": "user", "content": content})
        elif role == "assistant":
            # Handle tool calls if present
            if "tool_calls" in msg:
                tool_calls = msg["tool_calls"]
                message_content = content if content else ""
                tool_use_blocks = []

                for tool_call in tool_calls:
                    tool_use_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "input": json.loads(tool_call["function"]["arguments"]),
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
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
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
        anthropic_tools.append(
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
            }
        )

    # Call the API
    # https://docs.anthropic.com/en/api/messages
    response = client.messages.create(
        model=model_id,
        system=system_content,
        messages=anthropic_messages,
        tools=anthropic_tools,
        max_tokens=8192,  # https://docs.anthropic.com/en/docs/about-claude/models/all-models
        temperature=0.0,
        timeout=TIMEOUT,
    )

    # Calculate tokens (approximation using OpenAI's tokenizer)
    token_input = count_tokens(messages=messages)
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

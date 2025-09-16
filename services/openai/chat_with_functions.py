# Standard imports
import json
from typing import Any, Optional, cast

# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat import ChatCompletionDeveloperMessageParam

# Local imports
from config import OPENAI_MODEL_ID_GPT_5, TIMEOUT
from services.openai.count_tokens import count_tokens
from services.openai.init import create_openai_client
from utils.error.handle_exceptions import handle_exceptions


def find_function_name(openai_messages: list[dict], tool_call_id: str):
    for msg in openai_messages:
        if "tool_calls" not in msg:
            continue

        for tool_call in msg["tool_calls"]:
            if tool_call["id"] == tool_call_id:
                return cast(str, tool_call["function"]["name"])

    return "unknown_function"


def convert_tool_result(block: dict, openai_messages: list[dict]):
    tool_call_id = cast(str, block.get("tool_use_id"))
    function_name = find_function_name(openai_messages, tool_call_id)
    content = cast(str, block.get("content", ""))

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": function_name,
        "content": content,
    }


@handle_exceptions(raise_on_error=True)
def chat_with_openai(
    messages: list[ChatCompletionMessageParam],
    system_content: str,
    tools: list[ChatCompletionToolParam],
    model_id: str = OPENAI_MODEL_ID_GPT_5,
) -> tuple[
    dict[str, Any],  # Response message
    Optional[str],  # Tool call ID
    Optional[str],  # Tool name
    Optional[dict],  # Tool args
    int,  # Input tokens
    int,  # Output tokens
]:
    # Convert Claude-format messages to OpenAI-specific format
    openai_messages: list[ChatCompletionMessageParam] = []

    for msg in messages:
        content = msg.get("content", "")

        if not isinstance(content, list):
            # Check if the message has tool_calls
            if "tool_calls" in msg:
                openai_messages.append(
                    {"role": msg.get("role", ""), "tool_calls": msg["tool_calls"]}
                )
            else:
                openai_messages.append(
                    cast(ChatCompletionMessageParam, {
                        "role": msg.get("role", ""),
                        "content": content,
                    })
                )
            continue

        # Handle messages with tool use
        if any(block.get("type") == "tool_use" for block in content):
            assistant_msg = {"role": "assistant", "tool_calls": []}

            for block in content:
                if block.get("type") == "text":
                    assistant_msg["content"] = block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_call = {
                        "id": block.get("id"),
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                        "type": "function",
                    }
                    assistant_msg["tool_calls"].append(tool_call)

            openai_messages.append(cast(ChatCompletionMessageParam, assistant_msg))

        # Handle tool result messages
        elif any(block.get("type") == "tool_result" for block in content):
            for block in content:
                if block.get("type") == "tool_result":
                    openai_messages.append(cast(ChatCompletionMessageParam, convert_tool_result(cast(dict, block), cast(list[dict], openai_messages))))

    # Prepare messages with system message
    system_message: ChatCompletionDeveloperMessageParam = {"role": "developer", "content": system_content}
    all_messages: list[ChatCompletionMessageParam] = [system_message] + openai_messages

    # https://platform.openai.com/docs/api-reference/chat/create?lang=python
    client: OpenAI = create_openai_client()
    completion: ChatCompletion = client.chat.completions.create(
        messages=all_messages,
        model=model_id,
        n=1,
        timeout=TIMEOUT,
        tools=tools,
        tool_choice="auto",  # DO NOT USE "required" and allow GitAuto not to call any tools.
    )

    choice: Choice = completion.choices[0]
    tool_calls = choice.message.tool_calls

    # Calculate tokens
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])

    # Handle tool calls and create response message
    response_message = {
        "role": choice.message.role,
        "content": choice.message.content or "",
    }

    if not tool_calls:
        return (
            response_message,
            None,  # tool_call_id
            None,  # tool_name
            None,  # tool_args
            token_input,
            token_output,
        )

    tool_call = tool_calls[0]
    tool_call_id = tool_call.id
    tool_call = cast(ChatCompletionMessageToolCall, tool_call)
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    response_message = cast(dict[str, Any], response_message)
    response_message["tool_calls"] = [
        {
            "id": tool_call_id,
            "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
            "type": "function",
        }
    ]

    # Remove empty content from response message
    if response_message["content"] == "":
        response_message.pop("content")

    return (
        response_message,
        tool_call_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )

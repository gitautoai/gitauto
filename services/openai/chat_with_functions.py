# Standard imports
import json
from typing import Any, Optional

# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)

# Local imports
from config import OPENAI_MODEL_ID_O3_MINI, TIMEOUT
from services.openai.count_tokens import count_tokens
from services.openai.init import create_openai_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_openai(
    messages: list[dict[str, Any]],
    system_content: str,
    tools: list[dict[str, Any]],
    model_id: str = OPENAI_MODEL_ID_O3_MINI,
) -> tuple[
    dict[str, Any],  # Response message
    Optional[str],  # Tool call ID
    Optional[str],  # Tool name
    Optional[dict],  # Tool args
    int,  # Input tokens
    int,  # Output tokens
]:
    # Prepare messages with system message
    system_message = {"role": "developer", "content": system_content}
    all_messages = [system_message] + messages

    # Create the client and call the API
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
    tool_calls: list[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Calculate tokens
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])

    # Handle tool calls and create response message
    response_message = {"role": choice.message.role, "content": choice.message.content}

    tool_call_id = None
    tool_name = None
    tool_args = None

    if tool_calls:
        tool_call = tool_calls[0]
        tool_call_id = tool_call.id
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        response_message["tool_calls"] = [
            {
                "id": tool_call_id,
                "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
                "type": "function",
            }
        ]

    return (
        response_message,
        tool_call_id,
        tool_name,
        tool_args,
        token_input,
        token_output,
    )

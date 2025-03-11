# Standard imports
import json
from typing import Dict, Any, List, Tuple, Optional

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
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_openai(
    messages: List[Dict[str, Any]],
    system_content: str,
    tools: List[Dict[str, Any]],
    model_id: str = OPENAI_MODEL_ID_O3_MINI,
) -> Tuple[
    Dict[str, Any],  # Response message
    Optional[str],  # Tool call ID
    Optional[str],  # Tool name
    Optional[Dict],  # Tool args
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
    tool_calls: List[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Calculate tokens
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])

    # Handle tool calls
    tool_call_id = None
    tool_name = None
    tool_args = None

    if tool_calls:
        tool_call_id = tool_calls[0].id
        tool_name = tool_calls[0].function.name
        tool_args = json.loads(tool_calls[0].function.arguments)

    return choice.message, tool_call_id, tool_name, tool_args, token_input, token_output

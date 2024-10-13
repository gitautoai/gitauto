# Standard imports
import json
from typing import Iterable, List

# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)

# Local imports
from config import OPENAI_MODEL_ID_GPT_4O, OPENAI_TEMPERATURE, TIMEOUT
from services.github.github_types import BaseArgs
from services.openai.functions import functions_to_call, TOOLS
from services.openai.init import create_openai_client
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def resolve_ticket(
    messages: Iterable[ChatCompletionMessageParam],
    base_args: BaseArgs,
    previous_calls: List[dict] = None,
):
    """https://platform.openai.com/docs/api-reference/chat/create"""
    if previous_calls is None:
        previous_calls = []

    client: OpenAI = create_openai_client()
    completion: ChatCompletion = client.chat.completions.create(
        messages=messages,
        model=OPENAI_MODEL_ID_GPT_4O,
        store=False,
        max_completion_tokens=None,
        n=1,
        seed=None,
        service_tier="auto",  # defaults to "auto"
        stop=None,
        stream=False,
        temperature=OPENAI_TEMPERATURE,
        timeout=TIMEOUT,
        tools=TOOLS,
        tool_choice="required",
        parallel_tool_calls=False,
    )
    choice: Choice = completion.choices[0]
    # print(f"choice: {choice}")
    tool_calls: List[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Return if no tool calls
    if not tool_calls:
        print("No tool calls: ", choice.message.content)
        # TODO: Update issue comment with this response
        return choice.message.content

    # Handle multiple tool calls
    tool_call_id: str = tool_calls[0].id
    tool_function_name: str = tool_calls[0].function.name
    print(f"tool_function_name: {tool_function_name}")
    tool_args: dict = json.loads(tool_calls[0].function.arguments)
    print(f"tool_args: {tool_args}")

    # Check if the same function with the same args has been called before
    current_call = {"function": tool_function_name, "args": tool_args}
    if current_call in previous_calls:
        function_result: str = (
            f"The function ({tool_function_name}) was called with the same arguments ({json.dumps(tool_args)}) as before. To prevent an infinite loop, this call will be skipped."
        )
        print(function_result)
    else:
        function_result = functions_to_call[tool_function_name](
            **tool_args, base_args=base_args
        )

    # Append the function call to the messages
    messages.append(choice.message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_function_name,
            "content": function_result,
        }
    )
    previous_calls.append(current_call)

    # Exit if the current call is in the previous calls
    if current_call in previous_calls:
        return messages

    # Recursively call this function
    return resolve_ticket(
        messages=messages, base_args=base_args, previous_calls=previous_calls
    )

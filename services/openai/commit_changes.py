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
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

# Local imports
from config import OPENAI_MODEL_ID_GPT_4O, OPENAI_TEMPERATURE, TIMEOUT
from services.github.github_types import BaseArgs
from services.openai.count_tokens import count_tokens
from services.openai.functions import (
    COMMIT_CHANGES_TO_REMOTE_BRANCH,
    functions_to_call,
    TOOLS,
)
from services.openai.init import create_openai_client
from services.openai.instructions.commit_changes import (
    SYSTEM_INSTRUCTION_FOR_COMMIT_CHANGES,
)
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def commit_changes(
    messages: Iterable[ChatCompletionMessageParam],
    base_args: BaseArgs,
    previous_calls: List[dict] | None = None,
    tools: Iterable[ChatCompletionToolParam] = None,
    total_token_input: int = 0,
    total_token_output: int = 0,
):
    """https://platform.openai.com/docs/api-reference/chat/create"""
    if tools is None:
        tools = TOOLS
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
        tools=tools,
        tool_choice="required",
        parallel_tool_calls=False,
    )
    choice: Choice = completion.choices[0]
    tool_calls: List[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Calculate tokens for this call
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])
    total_token_input += token_input
    total_token_output += token_output

    # Return if no tool calls
    if not tool_calls:
        print("No tool calls: ", choice.message.content)
        # TODO: Update issue comment with this response
        return messages, total_token_input, total_token_output

    # Handle multiple tool calls
    tool_call_id: str = tool_calls[0].id
    tool_name: str = tool_calls[0].function.name
    tool_args: dict = json.loads(tool_calls[0].function.arguments)
    print(f"tool_name: {tool_name}")
    print(f"tool_args: {tool_args}\n")

    # Check if the same function with the same args has been called before
    current_call = {"function": tool_name, "args": tool_args}
    if current_call in previous_calls:
        function_result: str = (
            f"The function ({tool_name}) was called with the same arguments ({json.dumps(tool_args)}) as before. To prevent an infinite loop, this call will be skipped.\n"
        )
        print(function_result)

        if len(tools) == 1:
            return messages, token_input, token_output

        # Replace the tool with the commit changes tool
        tools = [{"type": "function", "function": COMMIT_CHANGES_TO_REMOTE_BRANCH}]
        messages[0]["content"] = SYSTEM_INSTRUCTION_FOR_COMMIT_CHANGES
    else:
        function_result = functions_to_call[tool_name](**tool_args, base_args=base_args)

    # Append the function call to the messages
    messages.append(choice.message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": function_result,
        }
    )
    previous_calls.append(current_call)

    # Recursively call this function
    return commit_changes(
        messages=messages,
        base_args=base_args,
        previous_calls=previous_calls,
        tools=tools,
        total_token_input=total_token_input,
        total_token_output=total_token_output,
    )

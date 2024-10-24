# Standard imports
import json
from typing import Iterable, List, Literal

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
from services.openai.count_tokens import count_tokens
from services.openai.functions import (
    TOOLS_TO_COMMIT_CHANGES,
    TOOLS_TO_EXPLORE_REPO,
    TOOLS_TO_GET_FILE,
    tools_to_call,
)
from services.openai.init import create_openai_client
from services.openai.instructions.commit_changes import (
    SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES,
)
from services.openai.instructions.explore_repo import SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def explore_repo_or_commit_changes(
    messages: Iterable[ChatCompletionMessageParam],
    base_args: BaseArgs,
    mode: Literal["commit", "explore", "get"],
    previous_calls: List[dict] | None = None,
):
    """https://platform.openai.com/docs/api-reference/chat/create"""
    if previous_calls is None:
        previous_calls = []

    # Set the system message based on the mode
    if mode == "commit":
        content = SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES
        tools = TOOLS_TO_COMMIT_CHANGES
        tool_choice = "required"
    elif mode == "explore":
        content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_EXPLORE_REPO
        tool_choice = "auto"
    elif mode == "get":
        content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_GET_FILE
        tool_choice = "auto"
    system_message: ChatCompletionMessageParam = {"role": "system", "content": content}
    all_messages = [system_message] + list(messages)

    # Create the client and call the API
    client: OpenAI = create_openai_client()
    completion: ChatCompletion = client.chat.completions.create(
        messages=all_messages,
        model=OPENAI_MODEL_ID_GPT_4O,
        n=1,
        temperature=OPENAI_TEMPERATURE,
        timeout=TIMEOUT,
        tools=tools,
        tool_choice=tool_choice,
        parallel_tool_calls=False,
    )
    choice: Choice = completion.choices[0]
    tool_calls: List[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Calculate tokens for this call
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])

    # Return if no tool calls
    is_done = False
    if not tool_calls:
        print(f"No tool called in '{mode}' mode")
        return messages, previous_calls, token_input, token_output, is_done

    # Handle multiple tool calls
    tool_call_id: str = tool_calls[0].id
    tool_name: str = tool_calls[0].function.name
    tool_args: dict = json.loads(tool_calls[0].function.arguments)
    print(f"tool_name: {tool_name}")
    print(f"tool_args: {tool_args}\n")

    # Check if the same function with the same args has been called before
    current_call = {"function": tool_name, "args": tool_args}
    if current_call in previous_calls:
        print(f"The function '{tool_name}' was called with the same arguments as before")
        tool_result: str = (
            f"The function '{tool_name}' was called with the same arguments as before, which is non-sense. You must open the file path in your tool args and update your diff content accordingly."
        )
    else:
        tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
        previous_calls.append(current_call)
        is_done = True

    # Append the function call to the messages
    messages.append(choice.message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": str(tool_result),
        }
    )

    # Return
    return messages, previous_calls, token_input, token_output, is_done

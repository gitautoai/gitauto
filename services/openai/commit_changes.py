# Standard imports
import json
from typing import Iterable, Literal

# Third-party imports
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)

# Local imports
from config import OPENAI_MODEL_ID_O3_MINI, TIMEOUT
from services.github.github_manager import update_comment
from services.github.github_types import BaseArgs
from services.openai.count_tokens import count_tokens
from services.openai.functions.functions import (
    TOOLS_TO_COMMIT_CHANGES,
    TOOLS_TO_EXPLORE_REPO,
    TOOLS_TO_GET_FILE,
    TOOLS_TO_SEARCH_GOOGLE,
    TOOLS_TO_UPDATE_COMMENT,
    tools_to_call,
)
from services.openai.init import create_openai_client
from services.openai.instructions.commit_changes import (
    SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES,
)
from services.openai.instructions.explore_repo import SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
from services.openai.instructions.search_google import (
    SYSTEM_INSTRUCTION_TO_SEARCH_GOOGLE,
)
from services.openai.instructions.update_comment import (
    SYSTEM_INSTRUCTION_TO_UPDATE_COMMENT,
)
from utils.colorize_log import colorize
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def chat_with_agent(
    messages: Iterable[ChatCompletionMessageParam],
    base_args: BaseArgs,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    previous_calls: list[dict] | None = None,
    recursion_count: int = 0,
    p: int = 0,
):
    """https://platform.openai.com/docs/api-reference/chat/create"""
    if previous_calls is None:
        previous_calls = []

    # Set the system message based on the mode
    if mode == "comment":
        content = SYSTEM_INSTRUCTION_TO_UPDATE_COMMENT
        tools = TOOLS_TO_UPDATE_COMMENT
    elif mode == "commit":
        content = SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES
        tools = TOOLS_TO_COMMIT_CHANGES
    elif mode == "explore":
        content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_EXPLORE_REPO
    elif mode == "get":
        content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_GET_FILE
    elif mode == "search":
        content = SYSTEM_INSTRUCTION_TO_SEARCH_GOOGLE
        tools = TOOLS_TO_SEARCH_GOOGLE

    # role: "developer" is recommended for o3-mini as of 2025-02-01 https://platform.openai.com/docs/guides/reasoning#advice-on-prompting
    system_message: ChatCompletionMessageParam = {
        "role": "developer",
        "content": content,
    }
    all_messages = [system_message] + list(messages)

    # Create the client and call the API
    client: OpenAI = create_openai_client()
    completion: ChatCompletion = client.chat.completions.create(
        messages=all_messages,
        model=OPENAI_MODEL_ID_O3_MINI,
        n=1,
        # temperature=OPENAI_TEMPERATURE,  # Not supported by o3-mini as of 2025-02-01
        timeout=TIMEOUT,
        tools=tools,
        tool_choice="auto",  # DO NOT USE "required" and allow GitAuto not to call any tools.
        # parallel_tool_calls=False,  # Not supported by o3-mini as of 2025-02-01
    )
    choice: Choice = completion.choices[0]
    tool_calls: list[ChatCompletionMessageToolCall] | None = choice.message.tool_calls

    # Calculate tokens for this call
    token_input = count_tokens(messages=messages)
    token_output = count_tokens(messages=[choice.message])

    # Return if no tool calls
    is_done = False
    if not tool_calls:
        print(colorize(f"No tools were called in '{mode}' mode", "yellow"))
        return messages, previous_calls, None, None, token_input, token_output, is_done

    # Handle multiple tool calls
    tool_call_id: str = tool_calls[0].id
    tool_name: str = tool_calls[0].function.name
    tool_args: dict = json.loads(tool_calls[0].function.arguments)
    # print(colorize(f"tool_name: {tool_name}", "green"))
    # print(colorize(f"tool_args: {tool_args}\n", "green"))

    # Check if the same function with the same args has been called before
    current_call = {"function": tool_name, "args": tool_args}
    if current_call in previous_calls:
        msg = f"The function '{tool_name}' was called with the same arguments as before"
        print(msg)
        tool_result = f"{msg}, which is non-sense. You must open the file path in your tool args and update your diff content accordingly."
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

    # Recursively call the function if the mode is "explore" and the tool was called
    if mode == "explore" and tool_calls and recursion_count < 3:
        msg = f"Calling `{tool_name}()` with `{tool_args}`..."
        update_comment(body=msg, base_args=base_args, p=p)
        return chat_with_agent(
            messages=messages,
            base_args=base_args,
            mode=mode,
            previous_calls=previous_calls,
            recursion_count=recursion_count + 1,
            p=p + 5,
        )

    # Return
    return (
        messages,
        previous_calls,
        tool_name,
        tool_args,
        token_input,
        token_output,
        is_done,
    )

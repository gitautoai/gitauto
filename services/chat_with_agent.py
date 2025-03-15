# Standard imports
import time
from typing import Iterable, Literal, Dict, Any, List

# Local imports
from config import ANTHROPIC_MODEL_ID_35, ANTHROPIC_MODEL_ID_37, OPENAI_MODEL_ID_O3_MINI
from services.anthropic.chat_with_functions import chat_with_claude
from services.github.github_manager import update_comment
from services.github.github_types import BaseArgs
from services.openai.chat_with_functions import chat_with_openai
from services.openai.functions.functions import (
    TOOLS_TO_COMMIT_CHANGES,
    TOOLS_TO_EXPLORE_REPO,
    TOOLS_TO_GET_FILE,
    TOOLS_TO_SEARCH_GOOGLE,
    TOOLS_TO_UPDATE_COMMENT,
    tools_to_call,
)
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
from utils.progress_bar import create_progress_bar


# Track when Claude models are rate limited until
_CLAUDE_35_RATE_LIMITED_UNTIL = 0
_CLAUDE_37_RATE_LIMITED_UNTIL = 0


@handle_exceptions(raise_on_error=True)
def chat_with_agent(
    messages: Iterable[Dict[str, Any]],
    base_args: BaseArgs,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    previous_calls: List[Dict] | None = None,
    recursion_count: int = 1,
    p: int = 0,
    model_id: str = ANTHROPIC_MODEL_ID_35,  # Default to Claude 3.5
    log_messages: List[str] | None = None,
):
    global _CLAUDE_35_RATE_LIMITED_UNTIL, _CLAUDE_37_RATE_LIMITED_UNTIL

    if previous_calls is None:
        previous_calls = []

    if log_messages is None:
        log_messages = []

    # Set the system message and tools based on the mode
    system_content = ""
    tools = []
    if mode == "comment":
        system_content = SYSTEM_INSTRUCTION_TO_UPDATE_COMMENT
        tools = TOOLS_TO_UPDATE_COMMENT
    elif mode == "commit":
        system_content = SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES
        tools = TOOLS_TO_COMMIT_CHANGES
    elif mode == "explore":
        system_content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_EXPLORE_REPO
    elif mode == "get":
        system_content = SYSTEM_INSTRUCTION_TO_EXPLORE_REPO
        tools = TOOLS_TO_GET_FILE
    elif mode == "search":
        system_content = SYSTEM_INSTRUCTION_TO_SEARCH_GOOGLE
        tools = TOOLS_TO_SEARCH_GOOGLE

    # Check if Claude models are rate limited and use fallback models accordingly
    if (
        model_id == ANTHROPIC_MODEL_ID_35
        and time.time() < _CLAUDE_35_RATE_LIMITED_UNTIL
    ):
        msg = "Claude 3.5 is currently rate limited, trying Claude 3.7"
        print(colorize(msg, "yellow"))
        model_id = ANTHROPIC_MODEL_ID_37

    # If we're now using Claude 3.7 and it's also rate limited, fall back to OpenAI
    if (
        model_id == ANTHROPIC_MODEL_ID_37
        and time.time() < _CLAUDE_37_RATE_LIMITED_UNTIL
    ):
        msg = "Claude 3.7 is also rate limited, using OpenAI model"
        print(colorize(msg, "yellow"))
        model_id = OPENAI_MODEL_ID_O3_MINI

    # Get the appropriate model provider
    if model_id in (OPENAI_MODEL_ID_O3_MINI,):
        provider = chat_with_openai
    else:
        provider = chat_with_claude

    try:
        # Perform chat completion
        (
            response_message,
            tool_call_id,
            tool_name,
            tool_args,
            token_input,
            token_output,
        ) = provider(
            messages=list(messages),
            system_content=system_content,
            tools=tools,
            model_id=model_id,
        )
    except Exception as e:  # pylint: disable=broad-except
        # Check if it's a rate limit error from Claude (429)
        if (
            model_id == ANTHROPIC_MODEL_ID_35
            and hasattr(e, "status_code")
            and e.status_code == 429  # pylint: disable=no-member
        ):
            # Mark Claude 3.5 as rate limited for the next minute
            _CLAUDE_35_RATE_LIMITED_UNTIL = time.time() + 60  # 60 seconds = 1 minute
            msg = "Claude 3.5 is rate limited, trying Claude 3.7"
            print(colorize(msg, "yellow"))

            # Try with Claude 3.7
            try:
                (
                    response_message,
                    tool_call_id,
                    tool_name,
                    tool_args,
                    token_input,
                    token_output,
                ) = chat_with_claude(
                    messages=list(messages),
                    system_content=system_content,
                    tools=tools,
                    model_id=ANTHROPIC_MODEL_ID_37,
                )
            except Exception as e2:  # pylint: disable=broad-except
                # Check if Claude 3.7 is also rate limited
                if (
                    hasattr(e2, "status_code") and e2.status_code == 429
                ):  # pylint: disable=no-member
                    # Mark Claude 3.7 as rate limited for the next minute
                    _CLAUDE_37_RATE_LIMITED_UNTIL = (
                        time.time() + 60
                    )  # 60 seconds = 1 minute
                    msg = "Claude 3.7 is also rate limited, using OpenAI model"
                    print(colorize(msg, "yellow"))

                    # Switch to OpenAI as final fallback
                    (
                        response_message,
                        tool_call_id,
                        tool_name,
                        tool_args,
                        token_input,
                        token_output,
                    ) = chat_with_openai(
                        messages=list(messages),
                        system_content=system_content,
                        tools=tools,
                        model_id=OPENAI_MODEL_ID_O3_MINI,
                    )
                else:
                    # Re-raise other exceptions from Claude 3.7
                    raise e2
        elif (
            model_id == ANTHROPIC_MODEL_ID_37
            and hasattr(e, "status_code")
            and e.status_code == 429  # pylint: disable=no-member
        ):
            # Mark Claude 3.7 as rate limited for the next minute
            _CLAUDE_37_RATE_LIMITED_UNTIL = time.time() + 60  # 60 seconds = 1 minute
            msg = "Claude 3.7 is rate limited, using OpenAI model"
            print(colorize(msg, "yellow"))

            # Switch to OpenAI
            (
                response_message,
                tool_call_id,
                tool_name,
                tool_args,
                token_input,
                token_output,
            ) = chat_with_openai(
                messages=list(messages),
                system_content=system_content,
                tools=tools,
                model_id=OPENAI_MODEL_ID_O3_MINI,
            )
        else:
            # Re-raise other exceptions
            raise

    # Return if no tool calls
    is_done = False
    if not tool_name:
        print(colorize(f"No tools were called in '{mode}' mode", "yellow"))
        return (
            messages,
            previous_calls,
            None,
            None,
            token_input,
            token_output,
            is_done,
            p,
        )

    # Check if the same function with the same args has been called before
    current_call = {"function": tool_name, "args": tool_args}
    print(f"Calling {current_call}...")
    if current_call in previous_calls:
        tool_result = f"Error: The function '{tool_name}' was already called with the same arguments '{tool_args}' as before. You need to either:\n1. Call the function with different arguments, or\n2. Call another function, or\n3. Stop calling the function."
        print(tool_result)
    else:
        if tool_name not in tools_to_call:
            tool_result = f"Error: The function '{tool_name}' does not exist in the available tools. Please use one of the available tools."
        else:
            tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
        previous_calls.append(current_call)
        is_done = True

    # Append the function call to the messages
    messages_list = list(messages)
    messages_list.append(response_message)
    messages_list.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": str(tool_result),
        }
    )

    # Recursively call the function if the mode is "explore" and the tool was called
    if mode == "explore" and tool_name and recursion_count < 3:
        if tool_name == "get_remote_file_content" and "line_number" in tool_args:
            line_info = (
                f" around line {tool_args['line_number']}"
                if tool_args["line_number"] > 1
                else ""
            )
            msg = f"Read `{tool_args['file_path']}`{line_info}..."
        elif tool_name == "get_remote_file_content" and "keyword" in tool_args:
            msg = f"Read `{tool_args['file_path']}` around keyword `{tool_args['keyword']}`..."
        elif tool_name == "get_remote_file_content":
            msg = f"Read `{tool_args['file_path']}`..."
        else:
            msg = f"Calling `{tool_name}()` with `{tool_args}`..."

        # Add message to log and update comment
        log_messages.append(msg)
        update_comment(
            body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
            base_args=base_args,
        )

        return chat_with_agent(
            messages=messages_list,
            base_args=base_args,
            mode=mode,
            previous_calls=previous_calls,
            recursion_count=recursion_count + 1,
            p=p + 5,
            model_id=model_id,
            log_messages=log_messages,
        )

    # Return
    return (
        messages_list,
        previous_calls,
        tool_name,
        tool_args,
        token_input,
        token_output,
        is_done,
        p,
    )

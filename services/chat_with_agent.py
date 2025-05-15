# Standard imports
from typing import Literal, Any

# Local imports
from config import OPENAI_MODEL_ID_O3_MINI
from services.anthropic.chat_with_functions import chat_with_claude
from services.github.comments.update_comment import update_comment
from services.github.github_types import BaseArgs
from services.model_selection import get_model, try_next_model
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
from utils.colors.colorize_log import colorize
from utils.error.handle_exceptions import handle_exceptions
from utils.progress_bar.progress_bar import create_progress_bar


@handle_exceptions(raise_on_error=True)
def chat_with_agent(
    messages: list[dict[str, Any]],
    base_args: BaseArgs,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    previous_calls: list[dict] | None = None,
    recursion_count: int = 1,
    p: int = 0,
    log_messages: list[str] | None = None,
):
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

    while True:
        current_model = get_model()
        provider = (
            chat_with_openai
            if current_model == OPENAI_MODEL_ID_O3_MINI
            else chat_with_claude
        )
        print(f"Using model: {current_model}")

        try:
            (
                response_message,
                tool_call_id,
                tool_name,
                tool_args,
                token_input,
                token_output,
            ) = provider(
                messages,
                system_content=system_content,
                tools=tools,
                model_id=current_model,
            )
            break

        except Exception:  # pylint: disable=broad-except
            has_next, _ = try_next_model()
            if not has_next:
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
    if current_call in previous_calls:
        tool_result = f"Error: The function '{tool_name}' was already called with the same arguments '{tool_args}' as before. You need to either:\n1. Call the function with different arguments, or\n2. Call another function, or\n3. Stop calling the function."
        print(tool_result)
    else:
        # Function name and argument validation
        corrected_tool = None

        # Case 1: Function exists but arguments suggest a different function
        if tool_name in tools_to_call:
            if (
                tool_name == "commit_changes_to_remote_branch"
                and "file_path" in tool_args
                and "diff" not in tool_args
                and "file_content" in tool_args
            ):
                corrected_tool = ("replace_remote_file_content", tool_args)
            elif tool_name == "replace_remote_file_content" and "diff" in tool_args:
                corrected_tool = ("commit_changes_to_remote_branch", tool_args)

        # Case 2: Function doesn't exist but has similar name
        else:
            similar_functions = {
                "create_remote_file": "replace_remote_file_content",
                "update_remote_file": "replace_remote_file_content",
                "modify_remote_file": "replace_remote_file_content",
            }
            if similar_name := similar_functions.get(tool_name):
                corrected_tool = (similar_name, tool_args)

        # Execute the appropriate function
        if corrected_tool:
            print(
                f"Warning: Redirecting call from '{tool_name}' to '{corrected_tool[0]}'"
            )
            tool_name = corrected_tool[0]
            tool_args = corrected_tool[1]

        if tool_name in tools_to_call:
            tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
            previous_calls.append(current_call)
            is_done = True
        else:
            tool_result = f"Error: The function '{tool_name}' does not exist in the available tools. Please use one of the available tools."

    # Append the function call to the messages
    messages.append(response_message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": str(tool_result),
        }
    )

    # Recursively call the function if the mode is "explore" and the tool was called
    if mode == "explore" and tool_name:
        if tool_name == "get_remote_file_content" and "line_number" in tool_args:
            line_info = (
                f" around line {tool_args['line_number']}"
                if tool_args["line_number"] > 1
                else ""
            )
            msg = f"Read `{tool_args['file_path']}`{line_info}."
        elif tool_name == "get_remote_file_content" and "keyword" in tool_args:
            msg = f"Read `{tool_args['file_path']}` around keyword `{tool_args['keyword']}`."
        elif tool_name == "get_remote_file_content":
            msg = f"Read `{tool_args['file_path']}`."
        elif tool_name == "search_remote_file_contents":
            file_list = []
            if isinstance(tool_result, str):
                result_lines = tool_result.split("\n")
                first_line = result_lines[0] if result_lines else ""
                if first_line.startswith("0 files found"):
                    file_list = []
                else:
                    file_list = [
                        line[2:] for line in result_lines if line.startswith("- ")
                    ]

            if file_list:
                msg = f"Searched repository for `{tool_args['query']}` and found: \n- {'\n- '.join(file_list)}\n"
            else:
                msg = f"Searched repository for `{tool_args['query']}` but found no matching files."

        # Claude sometimes tries to call functions that don't exist in the list of tools...
        elif (
            tool_name
            in [
                "commit_changes_to_remote_branch",
                "replace_remote_file_content",
            ]
            and "file_path" in tool_args
        ):
            msg = f"Committed changes to `{tool_args['file_path']}`."
        else:
            msg = f"Calling `{tool_name}()` with `{tool_args}`."

        # Add message to log and update comment
        log_messages.append(msg)
        update_comment(
            body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
            base_args=base_args,
        )

        if recursion_count < 3:
            return chat_with_agent(
                messages=messages,
                base_args=base_args,
                mode=mode,
                previous_calls=previous_calls,
                recursion_count=recursion_count + 1,
                p=p + 5,
                log_messages=log_messages,
            )

    elif mode == "search" and tool_name:
        if tool_name == "search_google" and "query" in tool_args:
            query = tool_args.get("query", "")
            if query.strip():
                msg = f"Googled `{query}` and went through the results."
                log_messages.append(msg)
                update_comment(
                    body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
                    base_args=base_args,
                )

    elif mode == "commit" and tool_name:
        if "file_path" in tool_args:
            file_path = tool_args.get("file_path", "")
            if file_path.strip():
                msg = f"Modified `{file_path}` and committed."
                log_messages.append(msg)
                update_comment(
                    body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
                    base_args=base_args,
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
        p + 5,
    )

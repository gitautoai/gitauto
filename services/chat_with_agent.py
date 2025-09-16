# Standard imports
from typing import Any, Literal

# Third party imports
from schemas.supabase.types import Repositories

# Local imports
from config import OPENAI_MODEL_ID_GPT_5
from services.anthropic.chat_with_functions import chat_with_claude
from services.github.comments.update_comment import update_comment
from services.github.types.github_types import BaseArgs
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
from services.supabase.usage.insert_usage import Trigger
from services.webhook.utils.create_system_message import create_system_message

# Local imports (Utils)
from utils.colors.colorize_log import colorize
from utils.error.handle_exceptions import handle_exceptions
from utils.number.is_valid_line_number import is_valid_line_number
from utils.progress_bar.progress_bar import create_progress_bar


@handle_exceptions(raise_on_error=True)
def chat_with_agent(
    messages: list[dict[str, Any]],
    trigger: Trigger,
    base_args: BaseArgs,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    repo_settings: Repositories | None,
    previous_calls: list[dict] | None = None,
    recursion_count: int = 1,
    p: int = 0,
    log_messages: list[str] | None = None,
):
    if previous_calls is None:
        previous_calls = []

    if log_messages is None:
        log_messages = []

    # Create the system content
    system_message = create_system_message(
        trigger=trigger, mode=mode, repo_settings=repo_settings
    )

    # Select the tools
    tools = []
    if mode == "comment":
        tools = TOOLS_TO_UPDATE_COMMENT
    elif mode == "commit":
        tools = TOOLS_TO_COMMIT_CHANGES
    elif mode == "explore":
        tools = TOOLS_TO_EXPLORE_REPO
    elif mode == "get":
        tools = TOOLS_TO_GET_FILE
    elif mode == "search":
        tools = TOOLS_TO_SEARCH_GOOGLE

    while True:
        current_model = get_model()
        provider = (
            chat_with_openai
            if current_model == OPENAI_MODEL_ID_GPT_5
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
                messages=messages,
                system_content=system_message,
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
                tool_name == "apply_diff_to_file"
                and isinstance(tool_args, dict)
                and "file_path" in tool_args
                and "diff" not in tool_args
                and "file_content" in tool_args
            ):
                corrected_tool = ("replace_remote_file_content", tool_args)
            elif (
                tool_name == "replace_remote_file_content"
                and isinstance(tool_args, dict)
                and "diff" in tool_args
            ):
                corrected_tool = ("apply_diff_to_file", tool_args)

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
            if isinstance(tool_args, dict):
                tool_args.pop("base_args", None)
                tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
            else:
                tool_result = tools_to_call[tool_name](base_args=base_args)
            previous_calls.append(current_call)
            is_done = True
        else:
            tool_result = f"Error: The function '{tool_name}' does not exist in the available tools. Please use one of the available tools."

    # Append the function call to the messages
    messages.append(response_message)
    messages.append(
        {
            "role": "user",  # Claude expects a user message for tool_result https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview#sequential-tools
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": str(tool_result),
                }
            ],
        }
    )

    # Initialize msg variable
    msg = ""

    # Recursively call the function if the mode is "explore" and the tool was called
    if tool_name == "get_remote_file_content" and isinstance(tool_args, dict):
        if "line_number" in tool_args:
            line_info = (
                f" around line {tool_args['line_number']}"
                if is_valid_line_number(tool_args["line_number"])
                else ""
            )
            msg = f"Read `{tool_args['file_path']}`{line_info}."
        elif "keyword" in tool_args:
            msg = f"Read `{tool_args['file_path']}` around keyword `{tool_args['keyword']}`."
        else:
            msg = f"Read `{tool_args['file_path']}`."

    elif tool_name == "search_remote_file_contents":
        file_list = []
        if isinstance(tool_result, str):
            result_lines = tool_result.split("\n")
            first_line = result_lines[0] if result_lines else ""
            if first_line.startswith("0 files found"):
                file_list = []
            else:
                file_list = [line[2:] for line in result_lines if line.startswith("- ")]

        if file_list and isinstance(tool_args, dict):
            msg = f"Searched repository for `{tool_args['query']}` and found: \n- {'\n- '.join(file_list)}\n"
        elif isinstance(tool_args, dict):
            msg = f"Searched repository for `{tool_args['query']}` but found no matching files."
        else:
            msg = "Searched repository but found no matching files."

    elif tool_name == "get_file_tree_list":
        if tool_result and isinstance(tool_result, list):
            file_list = tool_result
            if (
                isinstance(tool_args, dict)
                and "dir_path" in tool_args
                and tool_args["dir_path"]
            ):
                msg = f"Listed contents of directory '{tool_args['dir_path']}': \n- {'\n- '.join(file_list)}\n"
            else:
                msg = f"Listed root directory contents: \n- {'\n- '.join(file_list)}\n"
        elif (
            isinstance(tool_args, dict)
            and "dir_path" in tool_args
            and tool_args["dir_path"]
        ):
            msg = f"Directory '{tool_args['dir_path']}' not found or is empty."
        else:
            msg = "Root directory is empty or not found."

    # Claude sometimes tries to call functions that don't exist in the list of tools...
    elif (
        tool_name in ["apply_diff_to_file", "replace_remote_file_content"]
        and isinstance(tool_args, dict)
        and "file_path" in tool_args
    ):
        msg = f"Committed changes to `{tool_args['file_path']}`."

    elif (
        tool_name == "search_google"
        and isinstance(tool_args, dict)
        and "query" in tool_args
    ):
        query = tool_args.get("query", "")
        if query.strip():
            msg = f"Googled `{query}` and went through the results."
            log_messages.append(msg)
            update_comment(
                body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
                base_args=base_args,
            )

    else:
        msg = f"Calling `{tool_name}()` with `{tool_args}`."

    # Add message to log and update comment
    if msg:
        log_messages.append(msg)
        update_comment(
            body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
            base_args=base_args,
        )

    if recursion_count < 3:
        return chat_with_agent(
            messages=messages,
            trigger=trigger,
            base_args=base_args,
            mode=mode,
            repo_settings=repo_settings,
            previous_calls=previous_calls,
            recursion_count=recursion_count + 1,
            p=p + 5,
            log_messages=log_messages,
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

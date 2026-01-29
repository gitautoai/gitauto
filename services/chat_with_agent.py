# Standard imports
import inspect
from typing import Any

# Third party imports
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

# Local imports
from config import OPENAI_MODEL_ID_GPT_5
from services.anthropic.chat_with_functions import chat_with_claude
from services.github.comments.update_comment import update_comment
from services.github.types.github_types import BaseArgs
from services.model_selection import get_model, try_next_model
from services.openai.chat_with_functions import chat_with_openai
from services.openai.functions.functions import FILE_EDIT_TOOLS, tools_to_call
from services.slack.slack_notify import slack_notify
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_target_test_file import is_target_test_file
from utils.files.is_test_file import is_test_file
from utils.formatting.collapse_list import collapse_list
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger
from utils.number.is_valid_line_number import is_valid_line_number
from utils.progress_bar.progress_bar import create_progress_bar


@handle_exceptions(raise_on_error=True)
async def chat_with_agent(
    *,
    messages: list[dict[str, Any]],
    system_message: str,
    base_args: BaseArgs,
    tools: list[ChatCompletionToolParam],
    p: int = 0,
    log_messages: list[str] | None = None,
    usage_id: int | None = None,
    allow_edit_any_file: bool = False,
    restrict_edit_to_target_test_file_only: bool = True,
):
    if log_messages is None:
        log_messages = []

    while True:
        current_model = get_model()
        logger.info("Using model: %s", current_model)

        try:
            provider = (
                chat_with_openai
                if current_model == OPENAI_MODEL_ID_GPT_5
                else chat_with_claude
            )
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
                usage_id=usage_id,
            )
            break

        except Exception:  # pylint: disable=broad-except
            has_next, _ = try_next_model()
            if not has_next:
                raise

    # Return if no tool calls (agent returned text without calling a tool)
    if not tool_name:
        logger.info("No tools were called. Response: %s", response_message)
        messages.append(response_message)
        is_completed = False
        return (
            messages,
            token_input,
            token_output,
            is_completed,
            p,
        )

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

    # Case 3: Function exists with wrong argument name
    if (
        tool_name == "replace_remote_file_content"
        and isinstance(tool_args, dict)
        and "new_content" in tool_args
    ):
        tool_args["file_content"] = tool_args.pop("new_content")

    # Execute the appropriate function
    if corrected_tool:
        logger.warning(
            "Redirecting call from '%s' to '%s'", tool_name, corrected_tool[0]
        )
        tool_name = corrected_tool[0]
        tool_args = corrected_tool[1]

    if tool_name in tools_to_call:
        is_file_edit_tool = tool_name in FILE_EDIT_TOOLS

        if is_file_edit_tool:
            file_path = (
                str(tool_args.get("file_path", ""))
                if isinstance(tool_args, dict)
                else ""
            )

            validation_error = None
            if (
                file_path
                and restrict_edit_to_target_test_file_only
                and not is_target_test_file(file_path, base_args)
            ):
                validation_error = (
                    f"Error: Cannot modify '{file_path}'. "
                    f"You can only create/edit/move/delete the test file for the target implementation file mentioned in the issue title."
                )
            elif file_path and not allow_edit_any_file and not is_test_file(file_path):
                validation_error = (
                    f"Error: Cannot modify non-test file '{file_path}'. "
                    f"This repository is in restricted mode - only test files can be created/edited/moved/deleted."
                )

            if validation_error:
                logger.error(validation_error)
                messages.append(response_message)
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call_id,
                                "content": validation_error,
                            }
                        ],
                    }
                )
                return await chat_with_agent(
                    messages=messages,
                    system_message=system_message,
                    base_args=base_args,
                    tools=tools,
                    p=p,
                    log_messages=log_messages,
                    usage_id=usage_id,
                    allow_edit_any_file=allow_edit_any_file,
                    restrict_edit_to_target_test_file_only=restrict_edit_to_target_test_file_only,
                )

        if isinstance(tool_args, dict):
            tool_args.pop("base_args", None)
            tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
        else:
            tool_result = tools_to_call[tool_name](base_args=base_args)
        if inspect.iscoroutine(tool_result):
            tool_result = await tool_result

        # Handle verify_task_is_complete result
        if tool_name == "verify_task_is_complete" and isinstance(tool_result, dict):
            is_success = tool_result.get("success", False)
            tool_message = tool_result.get("message", "")
            messages.append(response_message)
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": tool_message,
                        }
                    ],
                }
            )
            if is_success:
                add_log_message(tool_message, log_messages)
                update_comment(
                    body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
                    base_args=base_args,
                )
            else:
                logger.warning(tool_message)
            return (
                messages,
                token_input,
                token_output,
                is_success,
                p + 5,
            )
    else:
        tool_result = f"Error: The function '{tool_name}' does not exist in the available tools. Please use one of the available tools."
        owner = base_args.get("owner", "unknown")
        repo = base_args.get("repo", "unknown")
        slack_notify(
            f"🚨 LLM tried to call unavailable tool:\n"
            f"Tool: `{tool_name}`\n"
            f"Args: `{tool_args}`\n"
            f"Repo: `{owner}/{repo}`"
        )

    # Append the function call to the messages
    logger.info("Tool called: %s. Response: %s", tool_name, response_message)
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
            line_number = tool_args["line_number"]
            line_info = (
                f" around line {line_number}"
                if isinstance(line_number, (int, str))
                and is_valid_line_number(line_number)
                else ""
            )
            msg = f"Read `{tool_args['file_path']}`{line_info}."
        elif "keyword" in tool_args:
            msg = f"Read `{tool_args['file_path']}` around keyword `{tool_args['keyword']}`."
        elif "start_line" in tool_args or "end_line" in tool_args:
            start = tool_args.get("start_line", "start")
            end = tool_args.get("end_line", "end")
            msg = f"Read `{tool_args['file_path']}` lines {start}-{end}."
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
            msg = f"Searched repository for `{tool_args['query']}` and found:\n{collapse_list(file_list)}\n"
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
                msg = f"Listed contents of directory '{tool_args['dir_path']}':\n{collapse_list(file_list)}\n"
            else:
                msg = f"Listed root directory contents:\n{collapse_list(file_list)}\n"
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
        query = str(tool_args.get("query", ""))
        if query.strip():
            msg = f"Googled `{query}` and went through the results."
            add_log_message(msg, log_messages)
            update_comment(
                body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
                base_args=base_args,
            )

    elif (
        tool_name == "delete_file"
        and isinstance(tool_args, dict)
        and "file_path" in tool_args
    ):
        msg = f"Deleted file `{tool_args['file_path']}`."

    elif (
        tool_name == "move_file"
        and isinstance(tool_args, dict)
        and "old_file_path" in tool_args
        and "new_file_path" in tool_args
    ):
        msg = f"Moved file from `{tool_args['old_file_path']}` to `{tool_args['new_file_path']}`."

    else:
        msg = f"Calling `{tool_name}()` with `{tool_args}`."

    # Add message to log and update comment
    if msg:
        add_log_message(msg, log_messages)
        update_comment(
            body=create_progress_bar(p=p + 5, msg="\n".join(log_messages)),
            base_args=base_args,
        )

    # Regular tool execution - not completed until verify_task_is_complete succeeds
    is_completed = False
    return (
        messages,
        token_input,
        token_output,
        is_completed,
        p + 5,
    )

# Standard imports
from dataclasses import dataclass
import inspect

# Third party imports
from anthropic.types import MessageParam, ToolResultBlockParam, ToolUnionParam

# Local imports
from constants.claude import ClaudeModelId
from services.agents.verify_task_is_complete import VerifyTaskIsCompleteResult
from services.claude.chat_with_claude import chat_with_claude
from services.claude.replace_old_file_content import replace_old_file_content
from services.claude.sanitize_tool_args import sanitize_tool_args
from services.claude.tools.file_modify_result import FileMoveResult, FileWriteResult
from services.github.comments.update_comment import update_comment
from services.github.types.github_types import BaseArgs
from services.model_selection import get_model, try_next_model
from services.claude.tools.tools import FILE_EDIT_TOOLS, tools_to_call
from services.slack.slack_notify import slack_notify
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_target_test_file import is_target_test_file
from utils.files.is_test_file import is_test_file
from utils.formatting.collapse_list import collapse_list
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger
from utils.number.is_valid_line_number import is_valid_line_number
from utils.progress_bar.progress_bar import create_progress_bar


@dataclass
class AgentResult:
    messages: list[MessageParam]
    token_input: int
    token_output: int
    is_completed: bool
    p: int
    is_planned: bool


@handle_exceptions(raise_on_error=True)
async def chat_with_agent(
    *,
    messages: list[MessageParam],
    system_message: str,
    base_args: BaseArgs,
    tools: list[ToolUnionParam],
    p: int = 0,
    log_messages: list[str] | None = None,
    usage_id: int | None = None,
    allow_edit_any_file: bool = False,
    restrict_edit_to_target_test_file_only: bool = True,
    allowed_to_edit_files: set[str],
    model_id: ClaudeModelId | None,
):
    if log_messages is None:
        log_messages = []

    while True:
        current_model = model_id or get_model()
        logger.info("Using model: %s", current_model)

        try:
            (
                response_message,
                tool_calls,
                token_input,
                token_output,
            ) = chat_with_claude(
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
    if not tool_calls:
        logger.info("No tools were called. Response: %s", response_message)
        messages.append(response_message)
        return AgentResult(
            messages=messages,
            token_input=token_input,
            token_output=token_output,
            is_completed=False,
            p=p,
            is_planned=False,
        )

    # Append assistant message before processing tool calls
    messages.append(response_message)

    # Process all tool calls
    tool_result_blocks: list[ToolResultBlockParam] = []
    log_msgs: list[str] = []
    is_completed = False
    num_tool_calls = len(tool_calls)
    logger.info("Processing %d tool call(s)", num_tool_calls)

    # pylint: disable-next=too-many-nested-blocks
    for i, tc in enumerate(tool_calls, start=1):
        tool_use_id = tc.id
        tool_name = tc.name
        tool_args = tc.args

        # --- Tool name/arg correction ---
        corrected_tool = None

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
        else:
            similar_functions = {
                "create_remote_file": "replace_remote_file_content",
                "update_remote_file": "replace_remote_file_content",
                "modify_remote_file": "replace_remote_file_content",
            }
            if similar_name := similar_functions.get(tool_name):
                corrected_tool = (similar_name, tool_args)

        if (
            tool_name == "replace_remote_file_content"
            and isinstance(tool_args, dict)
            and "new_content" in tool_args
        ):
            tool_args["file_content"] = tool_args.pop("new_content")

        if corrected_tool:
            logger.warning(
                "Redirecting call from '%s' to '%s'", tool_name, corrected_tool[0]
            )
            tool_name = corrected_tool[0]
            tool_args = corrected_tool[1]

        if isinstance(tool_args, dict):
            sanitize_tool_args(tool_args)

        # --- Execute tool ---
        tool_result = None
        tool_result_content = ""
        msg = ""

        if tool_name in tools_to_call:
            is_file_edit_tool = tool_name in FILE_EDIT_TOOLS

            # File edit validation
            if is_file_edit_tool:
                file_path = (
                    str(tool_args.get("file_path", ""))
                    if isinstance(tool_args, dict)
                    else ""
                )

                validation_error = None
                is_in_allowed_to_edit_files = any(
                    file_path.endswith(f) for f in allowed_to_edit_files
                )
                is_target = is_target_test_file(file_path, base_args)
                if (
                    file_path
                    and restrict_edit_to_target_test_file_only
                    and not is_target
                    and not is_in_allowed_to_edit_files
                ):
                    validation_error = (
                        f"Error: Cannot modify '{file_path}'. "
                        f"file_path={file_path}, restrict_edit_to_target_test_file_only={restrict_edit_to_target_test_file_only}, "
                        f"is_target_test_file={is_target}, is_in_allowed_to_edit_files={is_in_allowed_to_edit_files}"
                    )
                elif (
                    file_path
                    and not allow_edit_any_file
                    and not is_test_file(file_path)
                    and not is_in_allowed_to_edit_files
                ):
                    validation_error = (
                        f"Error: Cannot modify '{file_path}'. "
                        f"file_path={file_path}, allow_edit_any_file={allow_edit_any_file}, "
                        f"is_test_file={is_test_file(file_path)}, is_in_allowed_to_edit_files={is_in_allowed_to_edit_files}"
                    )

                if validation_error:
                    logger.error(validation_error)
                    tool_result_blocks.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": validation_error,
                        }
                    )
                    continue

            # Execute the tool
            if isinstance(tool_args, dict):
                tool_args.pop("base_args", None)
                tool_result = tools_to_call[tool_name](**tool_args, base_args=base_args)
            else:
                tool_result = tools_to_call[tool_name](base_args=base_args)
            if inspect.iscoroutine(tool_result):
                tool_result = await tool_result

            # Handle verify_task_is_complete
            if tool_name == "verify_task_is_complete" and isinstance(
                tool_result, VerifyTaskIsCompleteResult
            ):
                is_completed = tool_result.success
                tool_result_content = tool_result.message
                if is_completed:
                    msg = tool_result.message
                else:
                    logger.warning(tool_result.message)
                    # Add files with errors to allowed_to_edit_files so the agent can fix them in the next iteration
                    if tool_result.error_files:
                        new_files = tool_result.error_files - allowed_to_edit_files
                        for f in new_files:
                            logger.info("Added %s to allowed_to_edit_files", f)
                        allowed_to_edit_files.update(new_files)
            else:
                # Format tool result content based on result type
                if isinstance(tool_result, FileWriteResult):
                    if tool_result.success and tool_result.content:
                        formatted_content = format_content_with_line_numbers(
                            file_path=tool_result.file_path,
                            content=tool_result.content,
                        )
                        tool_result_content = (
                            f"{tool_result.message}\n\n{formatted_content}"
                        )
                    else:
                        tool_result_content = tool_result.message
                elif isinstance(tool_result, FileMoveResult):
                    tool_result_content = tool_result.message
                else:
                    tool_result_content = str(tool_result)
        else:
            tool_result_content = f"Error: The function '{tool_name}' does not exist in the available tools. Please use one of the available tools."
            owner = base_args.get("owner", "unknown")
            repo = base_args.get("repo", "unknown")
            slack_notify(
                f"🚨 LLM tried to call unavailable tool:\n"
                f"Tool: `{tool_name}`\n"
                f"Args: `{tool_args}`\n"
                f"Repo: `{owner}/{repo}`"
            )

        logger.info(
            "Tool call %d/%d: %s, args: %s", i, num_tool_calls, tool_name, tool_args
        )
        logger.info(
            "Tool call %d/%d result: %s", i, num_tool_calls, tool_result_content
        )

        tool_result_blocks.append(
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": tool_result_content,
            }
        )

        # --- Build log message ---
        if (
            tool_name == "get_remote_file_content"
            and isinstance(tool_args, dict)
            and isinstance((file_path := tool_args.get("file_path")), str)
            and file_path
        ):
            first_line = tool_result_content.split("\n")[0]
            identifier = first_line[3:] if first_line.startswith("```") else file_path
            is_full_file_read = identifier == file_path
            replace_old_file_content(
                messages, identifier, is_full_file_read=is_full_file_read
            )

            if "line_number" in tool_args:
                line_number = tool_args["line_number"]
                line_info = (
                    f" around line {line_number}"
                    if isinstance(line_number, (int, str))
                    and is_valid_line_number(line_number)
                    else ""
                )
                msg = f"Read `{file_path}`{line_info}."
            elif "keyword" in tool_args:
                msg = f"Read `{file_path}` around keyword `{tool_args['keyword']}`."
            elif "start_line" in tool_args or "end_line" in tool_args:
                start = tool_args.get("start_line", "start")
                end = tool_args.get("end_line", "end")
                msg = f"Read `{file_path}` lines {start}-{end}."
            else:
                msg = f"Read `{file_path}`."

        elif tool_name in ("search_local_file_contents", "search_remote_file_contents"):
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
                    msg = (
                        f"Listed root directory contents:\n{collapse_list(file_list)}\n"
                    )
            elif (
                isinstance(tool_args, dict)
                and "dir_path" in tool_args
                and tool_args["dir_path"]
            ):
                msg = f"Directory '{tool_args['dir_path']}' not found or is empty."
            else:
                msg = "Root directory is empty or not found."

        elif (
            tool_name in ["apply_diff_to_file", "replace_remote_file_content"]
            and isinstance(tool_args, dict)
            and isinstance((file_path := tool_args.get("file_path")), str)
            and file_path
        ):
            replace_old_file_content(messages, file_path, is_full_file_read=True)
            msg = f"Committed changes to `{file_path}`."

        elif (
            tool_name == "search_google"
            and isinstance(tool_args, dict)
            and isinstance((query := tool_args.get("query")), str)
            and query.strip()
        ):
            msg = f"Googled `{query}` and went through the results."

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

        elif not msg:
            msg = f"Calling `{tool_name}()` with `{tool_args}`."

        if msg:
            log_msgs.append(msg)

    # Add all log messages and update comment once
    for msg in log_msgs:
        add_log_message(msg, log_messages)
    if log_msgs:
        update_comment(
            body=create_progress_bar(
                p=p + 5 * len(tool_calls), msg="\n".join(log_messages)
            ),
            base_args=base_args,
        )

    # Append all tool results as a single user message
    # https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview
    tool_result_msg: MessageParam = {
        "role": "user",
        "content": tool_result_blocks,
    }
    messages.append(tool_result_msg)

    return AgentResult(
        messages=messages,
        token_input=token_input,
        token_output=token_output,
        is_completed=is_completed,
        p=p + 5 * len(tool_calls),
        is_planned=False,
    )

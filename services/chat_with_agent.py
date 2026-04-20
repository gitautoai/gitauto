# Standard imports
import asyncio
from dataclasses import dataclass
from difflib import unified_diff
import inspect

# Third party imports
from anthropic.types import MessageParam, ToolResultBlockParam, ToolUnionParam

# Local imports
from constants.models import ModelId
from services.agents.verify_task_is_complete import VerifyTaskIsCompleteResult
from services.chat_with_model import chat_with_model
from services.claude.exceptions import ClaudeOverloadedError
from services.claude.remove_outdated_messages import remove_outdated_messages
from services.claude.sanitize_tool_args import sanitize_tool_args
from services.claude.tools.file_modify_result import (
    FileDeleteResult,
    FileMoveResult,
    FileWriteResult,
)
from services.claude.file_tracking import FILE_EDIT_TOOLS
from services.claude.tools.tools import tools_to_call
from services.github.comments.update_comment import update_comment
from services.get_fallback_models import get_fallback_models
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.formatting.collapse_list import collapse_list
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger
from utils.number.is_valid_line_number import is_valid_line_number
from utils.progress_bar.progress_bar import create_progress_bar


@dataclass
class AgentResult:  # pylint: disable=too-many-instance-attributes
    messages: list[MessageParam]
    token_input: int
    token_output: int
    cost_usd: float
    is_completed: bool
    completion_reason: str
    p: int
    is_planned: bool
    concurrent_push_detected: bool = False


@handle_exceptions(raise_on_error=True)
async def chat_with_agent(
    *,
    messages: list[MessageParam],
    system_message: str,
    base_args: BaseArgs,
    tools: list[ToolUnionParam],
    p: int = 0,
    log_messages: list[str] | None = None,
    usage_id: int,
    model_id: ModelId,
):
    if log_messages is None:
        logger.info(
            "chat_with_agent: log_messages arg is None; initializing to empty list for this call"
        )
        log_messages = []

    fallbacks = get_fallback_models(model_id)
    max_overload_retries = 2
    overload_retries = 0
    current_model = model_id
    fallback_index = 0

    while True:
        logger.info("Using model: %s", current_model)
        remove_outdated_messages(messages, file_paths_to_remove=set())

        try:
            llm_result = chat_with_model(
                messages=messages,
                system_content=system_message,
                tools=tools,
                model_id=current_model,
                usage_id=usage_id,
                created_by=f"{base_args['sender_id']}:{base_args['sender_name']}",
            )
            logger.info(
                "chat_with_model returned for %s; breaking retry loop", current_model
            )
            break

        except ClaudeOverloadedError:
            overload_retries += 1
            if overload_retries <= max_overload_retries:
                logger.info(
                    "chat_with_agent: ClaudeOverloadedError attempt %d/%d on %s; backing off before retry",
                    overload_retries,
                    max_overload_retries,
                    current_model,
                )
                delay = overload_retries * 5
                logger.warning(
                    "Overloaded (529), retrying %s in %ds (attempt %d/%d)",
                    current_model,
                    delay,
                    overload_retries,
                    max_overload_retries,
                )
                await asyncio.sleep(delay)
                logger.info(
                    "chat_with_agent: continuing retry loop after backoff sleep"
                )
                continue

            overload_retries = 0
            if fallback_index >= len(fallbacks):
                logger.error("All models exhausted after overload retries, raising")
                raise

            previous_model = current_model
            current_model = fallbacks[fallback_index]
            fallback_index += 1
            logger.warning(
                "Overload retries exhausted for %s, falling back to %s",
                previous_model,
                current_model,
            )

        except Exception:  # pylint: disable=broad-except
            if fallback_index >= len(fallbacks):
                logger.error("All models exhausted, raising")
                raise

            previous_model = current_model
            current_model = fallbacks[fallback_index]
            fallback_index += 1
            logger.warning(
                "Error with %s, falling back to %s",
                previous_model,
                current_model,
            )

    # Return if no tool calls (agent returned text without calling a tool)
    if not llm_result.tool_calls:
        logger.info("No tools were called. Response: %s", llm_result.assistant_message)
        messages.append(llm_result.assistant_message)
        logger.info(
            "chat_with_agent: returning early AgentResult with no tool calls for this turn"
        )
        return AgentResult(
            messages=messages,
            token_input=llm_result.token_input,
            token_output=llm_result.token_output,
            cost_usd=llm_result.cost_usd,
            is_completed=False,
            completion_reason="",
            p=p,
            is_planned=False,
        )

    # Append assistant message before processing tool calls
    messages.append(llm_result.assistant_message)

    # Extract text from the assistant message for completion context
    content = llm_result.assistant_message["content"]
    if isinstance(content, str):
        logger.info(
            "chat_with_agent: assistant_message.content is a plain str; using as-is for completion context"
        )
        assistant_text = content
    else:
        logger.info(
            "chat_with_agent: assistant_message.content is a block list; joining text blocks for completion context"
        )
        assistant_text = "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )

    # Process all tool calls
    tool_result_blocks: list[ToolResultBlockParam] = []
    log_msgs: list[str] = []
    is_completed = False
    concurrent_push_detected = False
    num_tool_calls = len(llm_result.tool_calls)
    logger.info("Processing %d tool call(s)", num_tool_calls)

    # pylint: disable-next=too-many-nested-blocks
    for i, tc in enumerate(llm_result.tool_calls, start=1):
        tool_use_id = tc.id
        tool_name = tc.name
        tool_args = tc.args

        # --- Tool name/arg correction ---
        corrected_tool = None

        if tool_name in tools_to_call:
            logger.info(
                "tool_name=%s is a known tool; checking for arg-shape corrections",
                tool_name,
            )
            if (
                tool_name == "apply_diff_to_file"
                and isinstance(tool_args, dict)
                and "file_path" in tool_args
                and "diff" not in tool_args
                and "file_content" in tool_args
            ):
                logger.info(
                    "Correcting apply_diff_to_file -> write_and_commit_file (got file_content, missing diff)"
                )
                corrected_tool = ("write_and_commit_file", tool_args)
            elif (
                tool_name == "write_and_commit_file"
                and isinstance(tool_args, dict)
                and "diff" in tool_args
            ):
                logger.info(
                    "Correcting write_and_commit_file -> apply_diff_to_file (got diff arg)"
                )
                corrected_tool = ("apply_diff_to_file", tool_args)
        else:
            logger.info(
                "tool_name=%s is unknown; checking similar_functions map for a redirect",
                tool_name,
            )
            similar_functions = {
                "create_remote_file": "write_and_commit_file",
                "update_remote_file": "write_and_commit_file",
                "modify_remote_file": "write_and_commit_file",
                "replace_remote_file_content": "write_and_commit_file",
                "search_replace": "search_and_replace",
            }
            if similar_name := similar_functions.get(tool_name):
                logger.info(
                    "Redirecting unknown tool %s to canonical %s",
                    tool_name,
                    similar_name,
                )
                corrected_tool = (similar_name, tool_args)

        if (
            tool_name == "write_and_commit_file"
            and isinstance(tool_args, dict)
            and "new_content" in tool_args
        ):
            logger.info(
                "Renaming write_and_commit_file arg new_content -> file_content for backward compat"
            )
            tool_args["file_content"] = tool_args.pop("new_content")

        if corrected_tool:
            logger.warning(
                "Redirecting call from '%s' to '%s'", tool_name, corrected_tool[0]
            )
            tool_name = corrected_tool[0]
            tool_args = corrected_tool[1]

        if isinstance(tool_args, dict):
            logger.info(
                "tool_args is a dict for %s; passing through sanitize_tool_args",
                tool_name,
            )
            sanitize_tool_args(tool_args)

        # --- Execute tool ---
        tool_result = None
        tool_result_content = ""
        msg = ""

        if tool_name in tools_to_call:
            logger.info("Dispatching to known tool %s", tool_name)
            is_file_edit_tool = tool_name in FILE_EDIT_TOOLS

            # Capture old GITAUTO.md content before edit for diff
            old_gitauto_md = ""
            is_gitauto_md = False
            if is_file_edit_tool:
                logger.info(
                    "%s is a file-edit tool; checking if target is GITAUTO.md",
                    tool_name,
                )
                file_path = (
                    str(tool_args.get("file_path", ""))
                    if isinstance(tool_args, dict)
                    else ""
                )
                is_gitauto_md = file_path.endswith("GITAUTO.md")

            if is_gitauto_md:
                logger.info(
                    "Edit targets GITAUTO.md; capturing pre-edit content for diff"
                )
                clone_dir = base_args.get("clone_dir", "")
                if clone_dir:
                    logger.info(
                        "clone_dir=%s present; reading existing GITAUTO.md", clone_dir
                    )
                    old_gitauto_md = (
                        read_local_file(file_path="GITAUTO.md", base_dir=clone_dir)
                        or ""
                    )

            # Execute the tool (messages passed for tools like forget_messages; others absorb via **_kwargs)
            if isinstance(tool_args, dict):
                logger.info("Invoking %s with dict tool_args (kwargs)", tool_name)
                # Pop keys we pass explicitly to avoid "got multiple values for keyword argument" TypeError
                tool_args.pop("base_args", None)
                tool_args.pop("messages", None)
                tool_result = tools_to_call[tool_name](
                    **tool_args, base_args=base_args, messages=messages
                )
            else:
                logger.info(
                    "Invoking %s with no model-supplied kwargs (tool_args=%r)",
                    tool_name,
                    tool_args,
                )
                # Model passed None or non-dict args (e.g. verify_task_is_complete with no args)
                tool_result = tools_to_call[tool_name](
                    base_args=base_args, messages=messages
                )
            if inspect.iscoroutine(tool_result):
                logger.info("tool_result from %s is a coroutine; awaiting", tool_name)
                tool_result = await tool_result

            # Handle verify_task_is_complete
            if tool_name == "verify_task_is_complete" and isinstance(
                tool_result, VerifyTaskIsCompleteResult
            ):
                logger.info(
                    "verify_task_is_complete returned success=%s", tool_result.success
                )
                is_completed = tool_result.success
                tool_result_content = tool_result.message

                if is_completed:
                    logger.info(
                        "verify_task_is_complete succeeded; resetting verify_consecutive_failures"
                    )
                    msg = tool_result.message
                    base_args["verify_consecutive_failures"] = 0
                else:
                    logger.warning(tool_result.message)

                    # Cap verify failures: if verify fails 3 times regardless of whether the error is identical or not, the agent is stuck. Force completion.
                    base_args["verify_consecutive_failures"] += 1
                    consecutive_failures = base_args["verify_consecutive_failures"]
                    if consecutive_failures > 3:
                        logger.warning(
                            "verify_task_is_complete failed %d consecutive times, forcing completion",
                            consecutive_failures,
                        )
                        is_completed = True
                        tool_result_content = (
                            f"{tool_result.message}\n\n"
                            "NOTE: This error has persisted for 3 consecutive attempts. "
                            "Stopping to avoid further cost."
                        )
            else:
                logger.info("Formatting tool_result for non-verify tool %s", tool_name)
                # Format tool result content based on result type
                if isinstance(tool_result, FileWriteResult):
                    logger.info(
                        "tool_result is FileWriteResult for %s (success=%s)",
                        tool_name,
                        tool_result.success,
                    )
                    if tool_result.success and tool_result.content:
                        logger.info(
                            "FileWriteResult success with content; formatting with line numbers + diff"
                        )
                        formatted_content = format_content_with_line_numbers(
                            file_path=tool_result.file_path,
                            content=tool_result.content,
                        )
                        diff_section = (
                            f"\n\nDiff:\n```\n{tool_result.diff}```"
                            if tool_result.diff
                            else ""
                        )
                        tool_result_content = f"{tool_result.message}{diff_section}\n\n{formatted_content}"
                    else:
                        logger.info(
                            "FileWriteResult failure or no content; passing message through as tool_result_content"
                        )
                        tool_result_content = tool_result.message
                elif isinstance(tool_result, FileMoveResult):
                    logger.info(
                        "tool_result is FileMoveResult for %s; using message directly",
                        tool_name,
                    )
                    tool_result_content = tool_result.message
                elif isinstance(tool_result, FileDeleteResult):
                    logger.info(
                        "tool_result is FileDeleteResult for %s; using message directly",
                        tool_name,
                    )
                    tool_result_content = tool_result.message
                else:
                    logger.info(
                        "tool_result for %s is plain value; str()ing for tool_result_content",
                        tool_name,
                    )
                    tool_result_content = str(tool_result)

                # Detect concurrent-push race signaled by git_commit_and_push up the chain. If set, finish recording this tool's result, then break out of the tool-dispatch loop so the handler can bail cleanly (post a truthful final comment, save usage, etc.). Continuing would let the agent mutate a branch that already advanced past us.
                if (
                    isinstance(
                        tool_result, (FileWriteResult, FileMoveResult, FileDeleteResult)
                    )
                    and tool_result.concurrent_push_detected
                ):
                    logger.warning(
                        "chat_with_agent: tool %s reported concurrent_push_detected; will short-circuit remaining %d tool calls this turn and return to handler for cleanup",
                        tool_name,
                        num_tool_calls - i,
                    )
                    concurrent_push_detected = True

            # Notify Slack when GITAUTO.md is created or updated
            if (
                is_file_edit_tool
                and is_gitauto_md
                and isinstance(tool_result, FileWriteResult)
                and tool_result.success
            ):
                logger.info(
                    "GITAUTO.md was successfully edited; building Slack notification with unified diff"
                )
                owner = base_args.get("owner", "unknown")
                repo = base_args.get("repo", "unknown")
                pr_number = base_args.get("pr_number", "?")
                diff_lines = list(
                    unified_diff(
                        old_gitauto_md.splitlines(keepends=True),
                        (tool_result.content or "").splitlines(keepends=True),
                        fromfile="GITAUTO.md (before)",
                        tofile="GITAUTO.md (after)",
                    )
                )
                diff_text = (
                    "".join(diff_lines)
                    if diff_lines
                    else "(new file)\n" + (tool_result.content or "")
                )
                slack_notify(
                    f"📝 GITAUTO.md updated in `{owner}/{repo}` (PR #{pr_number}):\n```\n{diff_text}\n```"
                )

        else:
            logger.warning(
                "Unknown tool %s called by LLM; returning error to the agent and notifying Slack",
                tool_name,
            )
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
            tool_name == "get_local_file_content"
            and isinstance(tool_args, dict)
            and isinstance((file_path := tool_args.get("file_path")), str)
            and file_path
        ):
            logger.info(
                "Building log message for get_local_file_content on %s", file_path
            )
            if "line_number" in tool_args:
                logger.info(
                    "get_local_file_content was scoped by line_number=%s",
                    tool_args["line_number"],
                )
                line_number = tool_args["line_number"]
                line_info = (
                    f" around line {line_number}"
                    if isinstance(line_number, (int, str))
                    and is_valid_line_number(line_number)
                    else ""
                )
                msg = f"Read `{file_path}`{line_info}."
            elif "keyword" in tool_args:
                logger.info(
                    "get_local_file_content was scoped by keyword=%s",
                    tool_args["keyword"],
                )
                msg = f"Read `{file_path}` around keyword `{tool_args['keyword']}`."
            elif "start_line" in tool_args or "end_line" in tool_args:
                logger.info("get_local_file_content was scoped by line range")
                start = tool_args.get("start_line", "start")
                end = tool_args.get("end_line", "end")
                msg = f"Read `{file_path}` lines {start}-{end}."
            else:
                logger.info(
                    "get_local_file_content read %s without narrowing args", file_path
                )
                msg = f"Read `{file_path}`."

        elif tool_name == "search_local_file_contents":
            logger.info("Building log message for search_local_file_contents")
            file_list = []
            if isinstance(tool_result, str):
                logger.info(
                    "search_local_file_contents returned a string; parsing result lines"
                )
                result_lines = tool_result.split("\n")
                first_line = result_lines[0] if result_lines else ""
                if first_line.startswith("0 files found"):
                    logger.info("search_local_file_contents reported 0 files found")
                    file_list = []
                else:
                    logger.info(
                        "search_local_file_contents returned matches; extracting file paths from '- ' lines"
                    )
                    file_list = [
                        line[2:] for line in result_lines if line.startswith("- ")
                    ]

            if file_list and isinstance(tool_args, dict):
                logger.info(
                    "Building hit-list message for search query=%s (%d files)",
                    tool_args.get("query"),
                    len(file_list),
                )
                msg = f"Searched repository for `{tool_args['query']}` and found:\n{collapse_list(file_list)}\n"
            elif isinstance(tool_args, dict):
                logger.info(
                    "Building no-match message for search query=%s",
                    tool_args.get("query"),
                )
                msg = f"Searched repository for `{tool_args['query']}` but found no matching files."
            else:
                logger.info(
                    "search_local_file_contents tool_args is not a dict; using generic no-match message"
                )
                msg = "Searched repository but found no matching files."

        elif tool_name == "get_local_file_tree":
            logger.info("Building log message for get_local_file_tree")
            if tool_result and isinstance(tool_result, list):
                logger.info("get_local_file_tree returned %d entries", len(tool_result))
                file_list = tool_result
                if (
                    isinstance(tool_args, dict)
                    and "dir_path" in tool_args
                    and tool_args["dir_path"]
                ):
                    logger.info(
                        "get_local_file_tree was scoped to dir=%s",
                        tool_args["dir_path"],
                    )
                    msg = f"Listed contents of directory '{tool_args['dir_path']}':\n{collapse_list(file_list)}\n"
                else:
                    logger.info("get_local_file_tree listed the root directory")
                    msg = (
                        f"Listed root directory contents:\n{collapse_list(file_list)}\n"
                    )
            elif (
                isinstance(tool_args, dict)
                and "dir_path" in tool_args
                and tool_args["dir_path"]
            ):
                logger.info(
                    "get_local_file_tree returned empty for dir=%s",
                    tool_args["dir_path"],
                )
                msg = f"Directory '{tool_args['dir_path']}' not found or is empty."
            else:
                logger.info("get_local_file_tree returned empty for root directory")
                msg = "Root directory is empty or not found."

        elif (
            tool_name
            in ["apply_diff_to_file", "search_and_replace", "write_and_commit_file"]
            and isinstance(tool_args, dict)
            and isinstance((file_path := tool_args.get("file_path")), str)
            and file_path
        ):
            logger.info(
                "Building log message for file-edit tool %s on %s", tool_name, file_path
            )
            if isinstance(tool_result, FileWriteResult):
                logger.info(
                    "Using FileWriteResult.message for progress log on %s", file_path
                )
                msg = tool_result.message
            else:
                logger.info(
                    "Tool result for %s is not FileWriteResult; using generic committed-changes message",
                    tool_name,
                )
                msg = f"Committed changes to `{file_path}`."

        # search_web handler removed: DDG CAPTCHAs bots, tool disabled in tools.py

        elif (
            tool_name == "web_fetch"
            and isinstance(tool_args, dict)
            and isinstance((url := tool_args.get("url")), str)
            and url.strip()
        ):
            logger.info("Building log message for web_fetch of %s", url)
            msg = f"Fetched content from `{url}`."

        elif (
            tool_name == "curl"
            and isinstance(tool_args, dict)
            and isinstance((url := tool_args.get("url")), str)
            and url.strip()
        ):
            logger.info("Building log message for curl of %s", url)
            msg = f"Fetched raw content from `{url}`."

        elif (
            tool_name == "delete_file"
            and isinstance(tool_args, dict)
            and "file_path" in tool_args
        ):
            logger.info(
                "Building log message for delete_file on %s", tool_args["file_path"]
            )
            msg = f"Deleted file `{tool_args['file_path']}`."

        elif (
            tool_name == "move_file"
            and isinstance(tool_args, dict)
            and "old_file_path" in tool_args
            and "new_file_path" in tool_args
        ):
            logger.info(
                "Building log message for move_file %s -> %s",
                tool_args["old_file_path"],
                tool_args["new_file_path"],
            )
            msg = f"Moved file from `{tool_args['old_file_path']}` to `{tool_args['new_file_path']}`."

        elif tool_name == "forget_messages" and isinstance(tool_args, dict):
            logger.info("Building log message for forget_messages")
            file_paths = tool_args.get("file_paths", [])
            count = len(file_paths) if isinstance(file_paths, list) else 0
            msg = f"Forgot {count} file(s) from context."
            slack_notify(
                f"🧪 forget_messages called: {file_paths}",
                thread_ts=base_args.get("slack_thread_ts"),
            )

        elif tool_name == "query_file" and isinstance(tool_args, dict):
            logger.info(
                "Building log message for query_file on %s",
                tool_args.get("file_path", ""),
            )
            msg = f"Queried `{tool_args.get('file_path', '')}`."
            slack_notify(
                f"🧪 query_file: {tool_args.get('file_path', '')}",
                thread_ts=base_args.get("slack_thread_ts"),
            )

        elif not msg:
            logger.info(
                "No specific log message for tool=%s; falling back to generic call message",
                tool_name,
            )
            msg = f"Calling `{tool_name}()` with `{tool_args}`."

        if msg:
            logger.info("Appending progress log message for tool %s", tool_name)
            log_msgs.append(msg)

        if concurrent_push_detected:
            logger.info(
                "chat_with_agent: breaking tool-dispatch loop at call %d/%d because a prior tool in this turn hit a concurrent push",
                i,
                num_tool_calls,
            )
            break

    # Add all log messages and update comment once
    for msg in log_msgs:
        add_log_message(msg, log_messages)
    if log_msgs:
        logger.info("Flushing %d progress log messages to PR comment", len(log_msgs))
        update_comment(
            body=create_progress_bar(
                p=p + 5 * len(llm_result.tool_calls), msg="\n".join(log_messages)
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

    logger.info(
        "chat_with_agent returning AgentResult (tool_calls=%d, is_completed=%s, concurrent_push_detected=%s)",
        len(llm_result.tool_calls),
        is_completed,
        concurrent_push_detected,
    )
    return AgentResult(
        messages=messages,
        token_input=llm_result.token_input,
        token_output=llm_result.token_output,
        cost_usd=llm_result.cost_usd,
        is_completed=is_completed,
        completion_reason=assistant_text,
        p=p + 5 * len(llm_result.tool_calls),
        is_planned=False,
        concurrent_push_detected=concurrent_push_detected,
    )

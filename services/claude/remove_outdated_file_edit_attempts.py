# Third party imports
from anthropic.types import MessageParam

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=lambda messages: messages)
def remove_outdated_file_edit_attempts(
    messages: list[MessageParam],
):
    if not messages:
        return messages

    # Track latest diff results by filename - store position and type (failed/successful/input)
    file_latest_positions = dict[str, tuple[int, str]]()

    # Map tool_use_id → filename so we can associate tool_results with their edit tool
    tool_use_id_to_filename = dict[str, str]()

    # First pass: find all diff-related content and track latest position for each file
    for i, msg in enumerate(messages):
        if not isinstance(msg.get("content"), list):
            continue

        for item in msg["content"]:
            if not isinstance(item, dict):
                continue

            # Check for tool_use with apply_diff_to_file (assistant sending diffs)
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "apply_diff_to_file"
            ):

                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for apply_diff_to_file: %s",
                        type(filename),
                    )
                    continue

                file_latest_positions[filename] = (i, "input")
                tool_use_id = item.get("id")
                if isinstance(tool_use_id, str):
                    tool_use_id_to_filename[tool_use_id] = filename
                continue

            # Check for tool_use with search_and_replace (assistant editing file)
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "search_and_replace"
            ):

                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for search_and_replace: %s",
                        type(filename),
                    )
                    continue
                file_latest_positions[filename] = (i, "search_replace")
                tool_use_id = item.get("id")
                if isinstance(tool_use_id, str):
                    tool_use_id_to_filename[tool_use_id] = filename
                continue

            # Check for tool_use with write_and_commit_file (assistant replacing file)
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "write_and_commit_file"
            ):

                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for write_and_commit_file: %s",
                        type(filename),
                    )
                    continue
                file_latest_positions[filename] = (i, "replace")
                tool_use_id = item.get("id")
                if isinstance(tool_use_id, str):
                    tool_use_id_to_filename[tool_use_id] = filename
                continue

            # Check for tool_result (user/system responses)
            if msg.get("role") != "user" or item.get("type") != "tool_result":
                continue

            content_str = str(item.get("content", ""))

            # Check for failed diffs
            if (
                "diff partially applied to the file:" in content_str
                and "But, some changes were rejected" in content_str
            ):

                start_marker = "diff partially applied to the file: "
                end_marker = ". But, some changes were rejected"
                start = content_str.find(start_marker)
                end = content_str.find(end_marker)
                if start == -1 or end == -1:
                    continue

                start += len(start_marker)
                filename = content_str[start:end]
                file_latest_positions[filename] = (i, "failed")
                continue

            # Check for successful diffs
            if (
                "diff applied to the file:" in content_str
                and "successfully by apply_diff_to_file" in content_str
            ):

                start_marker = "diff applied to the file: "
                end_marker = " successfully by apply_diff_to_file"
                start = content_str.find(start_marker)
                end = content_str.find(end_marker)
                if start == -1 or end == -1:
                    continue

                start += len(start_marker)
                filename = content_str[start:end]
                file_latest_positions[filename] = (i, "successful")
                continue

            # Note: tool_results for search_and_replace/write_and_commit_file are NOT tracked here because their positions would make the latest tool_use look outdated.
            # They're handled in the second pass via tool_use_id_to_filename mapping.

    # Second pass: replace outdated content with placeholders
    for i, msg in enumerate(messages):
        if not isinstance(msg.get("content"), list):
            continue

        new_content = []
        for item in msg["content"]:
            # Use early continue to reduce nesting
            if not isinstance(item, dict):
                new_content.append(item)
                continue

            # Handle assistant apply_diff_to_file
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "apply_diff_to_file"
            ):
                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    new_content.append(item)
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for apply_diff_to_file: %s",
                        type(filename),
                    )
                    new_content.append(item)
                    continue

                latest_info = file_latest_positions.get(filename)
                if not latest_info or i >= latest_info[0]:
                    new_content.append(item)
                    continue

                new_item = dict(item)
                new_input = dict(input_data)
                if "diff" in new_input:
                    new_input["diff"] = "[Outdated diff input removed]"
                new_item["input"] = new_input
                new_content.append(new_item)
                continue

            # Handle assistant search_and_replace
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "search_and_replace"
            ):
                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    new_content.append(item)
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for search_and_replace: %s",
                        type(filename),
                    )
                    new_content.append(item)
                    continue
                latest_info = file_latest_positions.get(filename)
                if not latest_info or i >= latest_info[0]:
                    new_content.append(item)
                    continue

                new_item = dict(item)
                new_input = dict(input_data)
                if "old_string" in new_input:
                    new_input["old_string"] = "[Outdated search text removed]"
                if "new_string" in new_input:
                    new_input["new_string"] = "[Outdated replacement text removed]"
                new_item["input"] = new_input
                new_content.append(new_item)
                continue

            # Handle assistant write_and_commit_file
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "write_and_commit_file"
            ):
                input_data = item.get("input")
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    new_content.append(item)
                    continue

                filename = input_data["file_path"]
                if not isinstance(filename, str):
                    logger.info(
                        "file_path is not str for write_and_commit_file: %s",
                        type(filename),
                    )
                    new_content.append(item)
                    continue
                latest_info = file_latest_positions.get(filename)
                if not latest_info or i >= latest_info[0]:
                    new_content.append(item)
                    continue

                new_item = dict(item)
                new_input = dict(input_data)
                if "file_content" in new_input:
                    new_input["file_content"] = (
                        "[file content removed because file was re-read or edited]"
                    )
                new_item["input"] = new_input
                new_content.append(new_item)
                continue

            # Handle user tool_results for edit tools via tool_use_id.
            # A result is outdated if there's a later tool_use for the same file (i < latest).
            # Using strict < because text-based tracking may set latest to a tool_result position.
            if msg.get("role") == "user" and item.get("type") == "tool_result":
                tool_use_id = item.get("tool_use_id")
                filename = (
                    tool_use_id_to_filename.get(tool_use_id)
                    if isinstance(tool_use_id, str)
                    else None
                )
                if filename:
                    latest_info = file_latest_positions.get(filename)
                    if latest_info and i < latest_info[0]:
                        new_item = dict(item)
                        new_item["content"] = (
                            f"[Outdated edit result for '{filename}' removed]"
                        )
                        new_content.append(new_item)
                        continue
                    # Result of the latest edit — keep as-is
                    new_content.append(item)
                    continue

            # Handle user failed diff results (text-based fallback for results without tool_use_id)
            is_failed_diff = (
                msg.get("role") == "user"
                and item.get("type") == "tool_result"
                and "diff partially applied to the file:"
                in str(item.get("content", ""))
                and "But, some changes were rejected" in str(item.get("content", ""))
            )
            if not is_failed_diff:
                new_content.append(item)
                continue

            content_str = str(item.get("content", ""))
            marker = "diff partially applied to the file: "
            marker_pos = content_str.find(marker)
            end = content_str.find(". But, some changes were rejected")
            if marker_pos == -1 or end == -1:
                new_content.append(item)
                continue

            start = marker_pos + len(marker)
            if start >= end:
                new_content.append(item)
                continue

            filename = content_str[start:end]
            latest_info = file_latest_positions.get(filename)
            if not latest_info or i >= latest_info[0]:
                new_content.append(item)
                continue

            new_item = dict(item)
            has_filename_above = (
                i > 0
                and isinstance(messages[i - 1].get("content"), list)
                and any(
                    isinstance(p, dict)
                    and p.get("type") == "tool_use"
                    and isinstance(p.get("input"), dict)
                    and p.get("input", {}).get("file_path") == filename
                    for p in messages[i - 1]["content"]
                )
            )
            new_item["content"] = (
                "[Outdated failed diff removed]"
                if has_filename_above
                else f"[Outdated failed diff for '{filename}' removed]"
            )
            new_content.append(new_item)

        if new_content != msg["content"]:
            messages[i]["content"] = new_content

    return messages

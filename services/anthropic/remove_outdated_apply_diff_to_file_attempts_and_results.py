# Standard imports
from copy import deepcopy

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda messages: messages)
def remove_outdated_apply_diff_to_file_attempts_and_results(messages: list[dict]):
    if not messages:
        return messages

    # Make a deep copy to avoid modifying the original
    result = deepcopy(messages)

    # Track latest diff results by filename - store position and type (failed/successful/input)
    file_latest_positions = {}

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

                input_data = item.get("input", {})
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    continue

                filename = input_data["file_path"]
                file_latest_positions[filename] = (i, "input")
                continue

            # Check for tool_use with replace_remote_file_content (assistant replacing file)
            if (
                msg.get("role") == "assistant"
                and item.get("type") == "tool_use"
                and item.get("name") == "replace_remote_file_content"
            ):

                input_data = item.get("input", {})
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    continue

                filename = input_data["file_path"]
                file_latest_positions[filename] = (i, "replace")
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
                input_data = item.get("input", {})
                if not isinstance(input_data, dict) or "file_path" not in input_data:
                    new_content.append(item)
                    continue

                filename = input_data["file_path"]
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

            # Handle user failed diff results
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
                    and p["input"].get("file_path") == filename
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
            result[i]["content"] = new_content

    return result

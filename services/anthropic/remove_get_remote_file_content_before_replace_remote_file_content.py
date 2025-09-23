# Standard imports
from copy import deepcopy

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda messages: messages)
def remove_get_remote_file_content_before_replace_remote_file_content(
    messages: list[dict],
):
    if not messages:
        return messages

    # Make a deep copy to avoid modifying the original
    result = deepcopy(messages)

    # Track latest file operations by filename - store position and type
    file_latest_positions = {}

    # First pass: find all file-related content and track latest position for each file
    for i, msg in enumerate(messages):
        if not isinstance(msg.get("content"), list):
            continue

        for item in msg["content"]:
            if not isinstance(item, dict):
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

            # Check for tool_result with file content (user/system responses)
            if msg.get("role") != "user" or item.get("type") != "tool_result":
                continue

            content_str = str(item.get("content", ""))
            if (
                not content_str.startswith("Opened file: '")
                or "' with line numbers" not in content_str
            ):
                continue

            start_marker = "Opened file: '"
            end_marker = "' with line numbers"
            start = content_str.find(start_marker)
            end = content_str.find(end_marker)
            if start == -1 or end == -1:
                continue

            start += len(start_marker)
            filename = content_str[start:end]
            file_latest_positions[filename] = (i, "content")

    # Second pass: replace outdated file content with placeholders
    for i, msg in enumerate(messages):
        if not isinstance(msg.get("content"), list):
            continue

        new_content = []
        for item in msg["content"]:
            if not isinstance(item, dict):
                new_content.append(item)
                continue

            # Only process tool_result from user
            if msg.get("role") != "user" or item.get("type") != "tool_result":
                new_content.append(item)
                continue

            content_str = str(item.get("content", ""))
            if (
                not content_str.startswith("Opened file: '")
                or "' with line numbers" not in content_str
            ):
                new_content.append(item)
                continue

            start_marker = "Opened file: '"
            end_marker = "' with line numbers"
            start = content_str.find(start_marker)
            end = content_str.find(end_marker)
            if start == -1 or end == -1:
                new_content.append(item)
                continue

            start += len(start_marker)
            filename = content_str[start:end]
            latest_info = file_latest_positions.get(filename)

            if latest_info is not None:
                latest_position, _ = latest_info
                if i < latest_position:
                    new_item = dict(item)
                    new_item["content"] = "[Outdated content removed]"
                    new_content.append(new_item)
                else:
                    new_content.append(item)
            else:
                new_content.append(item)

        if new_content != msg["content"]:
            result[i]["content"] = new_content

    return result

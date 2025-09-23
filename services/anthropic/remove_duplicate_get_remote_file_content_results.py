# Standard imports
from copy import deepcopy

# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda messages: messages)
def remove_duplicate_get_remote_file_content_results(messages: list[dict]):
    if not messages:
        return messages

    # Make a deep copy to avoid modifying the original
    result = deepcopy(messages)

    # Track get_remote_file_content by filename - store the latest position for each file
    file_latest_positions = {}

    # First pass: find all get_remote_file_content tool results and track latest position for each file
    for i, msg in enumerate(messages):
        if msg.get("role") != "user" or not isinstance(msg.get("content"), list):
            continue

        for item in msg["content"]:
            if not isinstance(item, dict) or item.get("type") != "tool_result":
                continue

            content_str = str(item.get("content", ""))
            if not content_str.startswith("Opened file: '"):
                continue

            if not (
                "with line numbers for your information." in content_str
                or "and found multiple occurrences of" in content_str
            ):
                continue

            start = content_str.find("'") + 1
            end = content_str.find("'", start)
            if start <= 0 or end <= start:
                continue

            filename = content_str[start:end]
            file_latest_positions[filename] = i

    # Second pass: replace earlier occurrences with placeholder
    for i, msg in enumerate(messages):
        if msg.get("role") != "user" or not isinstance(msg.get("content"), list):
            continue

        new_content = []
        for item in msg["content"]:
            if not isinstance(item, dict) or item.get("type") != "tool_result":
                new_content.append(item)
                continue

            content_str = str(item.get("content", ""))
            if not content_str.startswith("Opened file: '"):
                new_content.append(item)
                continue

            if not (
                "with line numbers for your information." in content_str
                or "and found multiple occurrences of" in content_str
            ):
                new_content.append(item)
                continue

            start = content_str.find("'") + 1
            end = content_str.find("'", start)
            if start <= 0 or end <= start:
                new_content.append(item)
                continue

            filename = content_str[start:end]
            latest_position = file_latest_positions.get(filename)
            if latest_position is not None and i < latest_position:
                new_item = dict(item)
                new_item["content"] = f"[Outdated '{filename}' content removed]"
                new_content.append(new_item)
            else:
                new_content.append(item)

        if new_content != msg["content"]:
            result[i]["content"] = new_content

    return result

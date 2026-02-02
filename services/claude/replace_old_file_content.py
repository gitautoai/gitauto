from typing import TypeGuard

from anthropic.types import MessageParam, ToolResultBlockParam

from utils.error.handle_exceptions import handle_exceptions


# TypeGuard needed because pyright can't narrow TypedDict unions based on key value checks.
# isinstance(item, dict) doesn't help because TypedDict IS dict at runtime.
def is_tool_result(item: object) -> TypeGuard[ToolResultBlockParam]:
    return isinstance(item, dict) and item.get("type") == "tool_result"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def replace_old_file_content(messages: list[MessageParam], file_path: str):
    """Replace old file content with placeholder when the same file is read again."""
    placeholder = f"[Outdated '{file_path}' content removed]"

    for msg in messages:
        # Skip assistant messages (file content only appears in user messages)
        if msg.get("role") != "user":
            continue

        content = msg.get("content")

        # Handle string content (initial file messages)
        if isinstance(content, str) and content.startswith(f"```{file_path}"):
            msg["content"] = placeholder
            continue

        # Handle list of content blocks (tool_result from get_remote_file_content)
        if not isinstance(content, list):
            continue

        for item in content:
            if not is_tool_result(item):
                continue

            item_content = item.get("content")
            if not isinstance(item_content, str):
                continue

            if item_content.startswith(f"```{file_path}"):
                item["content"] = placeholder

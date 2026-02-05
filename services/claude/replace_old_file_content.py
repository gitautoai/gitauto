from typing import TypeGuard

from anthropic.types import MessageParam, ToolResultBlockParam

from utils.error.handle_exceptions import handle_exceptions


# TypeGuard needed because pyright can't narrow TypedDict unions based on key value checks.
# isinstance(item, dict) doesn't help because TypedDict IS dict at runtime.
def is_tool_result(item: object) -> TypeGuard[ToolResultBlockParam]:
    return isinstance(item, dict) and item.get("type") == "tool_result"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def replace_old_file_content(
    messages: list[MessageParam], identifier: str, is_full_file_read: bool
):
    """Replace old file content with placeholder.

    - Full file read (is_full_file_read=True): identifier is file_path, removes ALL content
    - Partial read (is_full_file_read=False): identifier is file_path#L10-L20, removes exact match only
    """
    placeholder = f"[Outdated '{identifier}' content removed]"

    for msg in messages:
        # Skip assistant messages (file content only appears in user messages)
        if msg.get("role") != "user":
            continue

        content = msg.get("content")

        # Handle string content (initial file messages)
        if isinstance(content, str):
            if is_full_file_read:
                if content.startswith(f"```{identifier}"):
                    msg["content"] = placeholder
            else:
                if content.startswith(f"```{identifier}\n"):
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

            if is_full_file_read:
                if item_content.startswith(f"```{identifier}"):
                    item["content"] = placeholder
            else:
                if item_content.startswith(f"```{identifier}\n"):
                    item["content"] = placeholder

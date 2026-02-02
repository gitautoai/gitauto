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
        # Skip assistant messages (file content only appears in user messages as tool_result)
        if msg.get("role") != "user" or not isinstance(
            (content_list := msg.get("content")), list
        ):
            continue

        for item in content_list:
            # Skip non-tool_result blocks (file content only comes from tool_result)
            if not is_tool_result(item):
                continue

            content = item.get("content")
            # get_remote_file_content always returns string content, skip non-string (e.g., list of blocks)
            if not isinstance(content, str):
                continue

            if content.startswith(f"```{file_path}"):
                item["content"] = placeholder

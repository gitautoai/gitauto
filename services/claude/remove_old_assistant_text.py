# Standard imports
from copy import deepcopy

# Third party imports
from anthropic.types import MessageParam

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Default keep_recent value
DEFAULT_KEEP_RECENT = 5


@handle_exceptions(default_return_value=lambda messages, **_: messages)
def remove_old_assistant_text(
    messages: list[MessageParam], keep_recent: int = DEFAULT_KEEP_RECENT
):
    if not messages:
        logger.info("No messages provided to remove_old_assistant_text")
        return messages

    # Make a deep copy to avoid mutating the original
    result = deepcopy(messages)

    # Find all assistant message indices
    assistant_indices = [
        i for i, msg in enumerate(messages) if msg.get("role") == "assistant"
    ]

    # Determine which ones to strip (all except the last N)
    if len(assistant_indices) <= keep_recent:
        logger.info(
            "Skipping remove_old_assistant_text: %d assistant messages <= keep_recent=%d",
            len(assistant_indices),
            keep_recent,
        )
        return result

    indices_to_strip = assistant_indices[:-keep_recent]
    stripped_count = 0

    for i in indices_to_strip:
        msg = result[i]
        content = msg.get("content", [])

        if not isinstance(content, list):
            continue

        # Keep only tool_use blocks, remove text blocks
        new_content = []
        had_text = False
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "tool_use":
                    new_content.append(item)
                elif item.get("type") == "text":
                    had_text = True
                    # Skip text blocks - they're the waste
            else:
                new_content.append(item)

        if had_text and new_content:
            result[i]["content"] = new_content
            stripped_count += 1

    if stripped_count > 0:
        logger.info(
            "Stripped text from %d old assistant messages (kept recent %d)",
            stripped_count,
            keep_recent,
        )
    return result

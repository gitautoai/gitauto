from anthropic.types import MessageParam

from services.claude.file_tracking import FilePosition
from utils.logging.logging_config import logger


def remove_outdated_user_messages(
    messages: list[MessageParam], latest_file_positions: dict[str, FilePosition]
):
    """Pop string user messages whose file was re-read or re-edited later via tools."""
    if not latest_file_positions:
        logger.info("No latest_file_positions entries, skipping user message removal")
        return

    indices_to_pop: list[int] = []
    for i, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue

        content = msg.get("content")
        if not isinstance(content, str):
            continue

        if not content.startswith("```"):
            continue

        first_newline = content.find("\n")
        if first_newline == -1:
            logger.info("msg[%d]: string starts with ``` but no newline", i)
            continue

        fp = content[3:first_newline]
        if fp in latest_file_positions:
            logger.info("msg[%d]: popping outdated string message for %s", i, fp)
            indices_to_pop.append(i)

    for i in reversed(indices_to_pop):
        messages.pop(i)

    if indices_to_pop:
        logger.info("Removed %d outdated string user messages", len(indices_to_pop))
    else:
        logger.info("No outdated string user messages found")

# Third party imports
from anthropic.types import MessageParam, ToolUnionParam

# Local imports
from services.claude.measure_messages_chars import measure_messages_chars
from services.claude.replace_old_file_content import replace_old_file_content
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

FORGET_MESSAGES: ToolUnionParam = {
    "name": "forget_messages",
    "description": (
        "Remove file contents from conversation history to save tokens. "
        "Use after reading reference files for pattern learning: once you've extracted "
        "the patterns you need, forget the file contents. Does NOT delete files from "
        "disk - only removes their content from the conversation context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths whose content should be removed from context.",
            },
        },
        "required": ["file_paths"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value="Failed to forget messages.", raise_on_error=False
)
def forget_messages(
    file_paths: list[str],
    messages: list[MessageParam],
    **_kwargs,
):
    chars_before = measure_messages_chars(messages)
    count = 0
    for fp in file_paths:
        logger.info("Forgetting file content for: %s", fp)
        replace_old_file_content(messages, fp, is_full_file_read=True)
        count += 1
    chars_after = measure_messages_chars(messages)
    chars_saved = chars_before - chars_after
    pct = (chars_saved / chars_before * 100) if chars_before else 0
    logger.info(
        "forget_messages: removed %d chars out of %d total (%.2g%%, %d remaining)",
        chars_saved,
        chars_before,
        pct,
        chars_after,
    )
    return f"Forgot {count} file(s) from context. Saved {chars_saved:,} chars ({pct:.2g}%, {chars_before:,} → {chars_after:,})."

from anthropic.types import MessageParam

from services.claude.replace_old_file_content import is_tool_result
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

VERIFY_PLACEHOLDER = "[Previous verify_task_is_complete result removed]"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def replace_old_verify_results(messages: list[MessageParam]):
    replaced_count = 0
    total_chars_saved = 0

    for msg in messages:
        if msg.get("role") != "user":
            continue

        content = msg.get("content")
        if not isinstance(content, list):
            continue

        for item in content:
            if not is_tool_result(item):
                continue

            item_content = item.get("content")
            if not isinstance(item_content, str):
                continue

            if item_content == VERIFY_PLACEHOLDER:
                continue

            if item_content.startswith(("Task NOT complete.", "Task completed.")):
                total_chars_saved += len(item_content) - len(VERIFY_PLACEHOLDER)
                item["content"] = VERIFY_PLACEHOLDER
                replaced_count += 1

    if replaced_count:
        logger.info(
            "Replaced %d old verify_task_is_complete results, saved %d chars",
            replaced_count,
            total_chars_saved,
        )
    else:
        logger.info("No previous verify_task_is_complete results to replace")

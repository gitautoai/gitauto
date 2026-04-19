from anthropic.types import MessageParam

from services.claude.detect_outdated_tool_ids import detect_outdated_tool_ids
from services.claude.remove_outdated_user_messages import remove_outdated_user_messages
from services.claude.remove_tool_pairs import remove_tool_pairs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def remove_outdated_messages(
    messages: list[MessageParam], file_paths_to_remove: set[str]
):
    """Orchestrator: detect and remove all outdated content from messages.

    1. detect_outdated_tool_ids scans messages and returns:
       - ids_to_remove: tool IDs whose file was re-read/re-edited later
       - latest_file_positions: dict[str, FilePosition], e.g. {
             "services/webhook/setup_handler.py": {"message_index": 5, "action": "read"},
             "services/claude/chat_with_claude.py": {"message_index": 12, "action": "edit"},
             "services/git/commit_file.py": {"message_index": 18, "action": "diff_success"},
             "services/jest/run_js_ts_test.py": {"message_index": 20, "action": "diff_failure"},
         }
         Anything earlier than these positions for the same file is outdated.
    2. remove_tool_pairs removes tool_use/tool_result blocks matching those IDs
    3. remove_outdated_user_messages pops string user messages like
       "```services/webhook/setup_handler.py\\n...```" if the file appears in latest_file_positions
    """
    if not messages:
        logger.info("No messages to optimize")
        return

    ids_to_remove, latest_file_positions = detect_outdated_tool_ids(
        messages, file_paths_to_remove=file_paths_to_remove
    )
    remove_tool_pairs(messages, ids_to_remove)
    remove_outdated_user_messages(messages, latest_file_positions)

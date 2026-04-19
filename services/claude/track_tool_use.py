from anthropic.types import ToolUseBlockParam

from services.claude.file_tracking import (
    FILE_EDIT_TOOLS,
    FileAction,
    FilePosition,
    FileReadEntry,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def track_tool_use(
    i: int,
    item: ToolUseBlockParam,
    file_paths_to_remove: set[str],
    latest_file_positions: dict[str, FilePosition],
    id_to_file: dict[str, str],
    id_to_msg_index: dict[str, int],
    file_read_ids: dict[str, list[FileReadEntry]],
):
    """Track a tool_use block for file reads and edits."""
    name = item.get("name")
    input_data = item.get("input")
    tool_id = item.get("id")

    if not isinstance(tool_id, str):
        logger.info("msg[%d]: tool_use missing string id", i)
        return

    is_read = name == "get_local_file_content"
    is_edit = name in FILE_EDIT_TOOLS
    if not (is_read or is_edit) or not isinstance(input_data, dict):
        return
    fp = input_data.get("file_path")
    if not isinstance(fp, str):
        return

    action: FileAction = "read" if is_read else "edit"
    logger.info("msg[%d]: tracked file %s for %s", i, action, fp)

    if fp not in file_paths_to_remove:
        latest_file_positions[fp] = FilePosition(message_index=i, action=action)
    else:
        logger.info("msg[%d]: %s is forced-outdated, skipping position update", i, fp)

    id_to_file[tool_id] = fp
    id_to_msg_index[tool_id] = i
    if is_read:
        file_read_ids.setdefault(fp, []).append(
            FileReadEntry(message_index=i, tool_id=tool_id)
        )

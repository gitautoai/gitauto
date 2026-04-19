from anthropic.types import MessageParam

from services.claude.extract_diff_result_file_path import extract_diff_result_file_path
from services.claude.file_tracking import (
    FILE_EDIT_TOOLS,
    FileAction,
    FilePosition,
    FileReadEntry,
)
from services.claude.track_tool_use import track_tool_use
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=(set(), {}), raise_on_error=False)
def detect_outdated_tool_ids(
    messages: list[MessageParam], file_paths_to_remove: set[str]
):
    """Scan messages to find outdated tool IDs for file reads, edits, and verifies."""
    latest_file_positions: dict[str, FilePosition] = {}

    # Files to remove: set their position beyond all messages so every occurrence is outdated
    if file_paths_to_remove:
        end = len(messages)
        for fp in file_paths_to_remove:
            logger.info("Marking all occurrences of %s as outdated (remove)", fp)
            latest_file_positions[fp] = FilePosition(message_index=end, action="remove")

    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}
    verify_ids: list[str] = []

    for i, msg in enumerate(messages):
        content = msg.get("content")
        if not isinstance(content, list):
            logger.info("msg[%d]: skipping non-list content", i)
            continue

        role = msg.get("role")

        for item in content:
            if not isinstance(item, dict):
                logger.info("msg[%d]: skipping non-dict item", i)
                continue

            # Use item["type"] (not .get) for pyright discriminated union narrowing
            if role == "assistant" and item["type"] == "tool_use":
                track_tool_use(
                    i,
                    item,
                    file_paths_to_remove,
                    latest_file_positions,
                    id_to_file,
                    id_to_msg_index,
                    file_read_ids,
                )

            elif role == "user" and item["type"] == "tool_result":
                tool_use_id = item.get("tool_use_id")
                if not isinstance(tool_use_id, str):
                    logger.info("msg[%d]: tool_result missing string tool_use_id", i)
                    continue

                item_content = item.get("content")
                if not isinstance(item_content, str):
                    logger.info("msg[%d]: tool_result content is not string", i)
                    continue

                if item_content.startswith(("Task NOT complete.", "Task completed.")):
                    logger.info("msg[%d]: tracked verify result %s", i, tool_use_id)
                    verify_ids.append(tool_use_id)

                # Track diff results (failed or successful)
                filename, diff_action = extract_diff_result_file_path(item)
                if filename:
                    logger.info("msg[%d]: tracked %s for %s", i, diff_action, filename)
                    if filename not in file_paths_to_remove:
                        use_idx = id_to_msg_index.get(tool_use_id, i)
                        action: FileAction = (
                            "diff_failure"
                            if diff_action == "diff_failure"
                            else "diff_success"
                        )
                        latest_file_positions[filename] = FilePosition(
                            message_index=use_idx, action=action
                        )
                    else:
                        logger.info(
                            "msg[%d]: %s is forced-outdated, skipping position update",
                            i,
                            filename,
                        )

    # --- Collect outdated IDs ---
    ids_to_remove: set[str] = set()

    # Outdated file reads
    for fp, entries in file_read_ids.items():
        latest = latest_file_positions.get(fp)
        if not latest:
            logger.info("No latest position for %s, skipping", fp)
            continue
        for msg_idx, tool_id in entries:
            if msg_idx < latest["message_index"]:
                logger.info(
                    "Outdated read of %s at msg[%d] (latest at msg[%d])",
                    fp,
                    msg_idx,
                    latest["message_index"],
                )
                ids_to_remove.add(tool_id)

    # Outdated file edits
    for i, msg in enumerate(messages):
        content = msg.get("content")
        if not isinstance(content, list):
            logger.info("msg[%d]: skipping non-list content (edit pass)", i)
            continue
        if msg.get("role") != "assistant":
            logger.info("msg[%d]: skipping non-assistant (edit pass)", i)
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                logger.info("msg[%d]: skipping non-tool_use block (edit pass)", i)
                continue
            if item.get("name") not in FILE_EDIT_TOOLS:
                logger.info("msg[%d]: skipping non-edit tool %s", i, item.get("name"))
                continue
            input_data = item.get("input")
            if not isinstance(input_data, dict):
                logger.info("msg[%d]: skipping non-dict input (edit pass)", i)
                continue
            fp = input_data.get("file_path")
            if not isinstance(fp, str):
                logger.info("msg[%d]: skipping non-string file_path (edit pass)", i)
                continue
            latest = latest_file_positions.get(fp)
            if latest and i < latest["message_index"]:
                tool_id = item.get("id")
                if isinstance(tool_id, str):
                    logger.info(
                        "Outdated edit of %s at msg[%d] (latest at msg[%d])",
                        fp,
                        i,
                        latest["message_index"],
                    )
                    ids_to_remove.add(tool_id)

    # Outdated tool_results for edits
    for i, msg in enumerate(messages):
        content = msg.get("content")
        if not isinstance(content, list):
            logger.info("msg[%d]: skipping non-list content (result pass)", i)
            continue
        if msg.get("role") != "user":
            logger.info("msg[%d]: skipping non-user (result pass)", i)
            continue
        for item in content:
            if not isinstance(item, dict):
                logger.info("msg[%d]: skipping non-dict item (result pass)", i)
                continue
            if item["type"] != "tool_result":
                logger.info("msg[%d]: skipping non-tool_result block (result pass)", i)
                continue
            tool_use_id = item.get("tool_use_id")
            if not isinstance(tool_use_id, str):
                logger.info("msg[%d]: skipping non-string tool_use_id (result pass)", i)
                continue
            if tool_use_id in ids_to_remove:
                logger.info("tool_result %s already marked for removal", tool_use_id)
                continue
            fp = id_to_file.get(tool_use_id)
            if not fp:
                fp, _ = extract_diff_result_file_path(item)
            if not fp:
                logger.info(
                    "msg[%d]: could not resolve file_path for %s", i, tool_use_id
                )
                continue
            latest = latest_file_positions.get(fp)
            if latest and i < latest["message_index"]:
                logger.info("Outdated tool_result for %s at msg[%d]", fp, i)
                ids_to_remove.add(tool_use_id)

    # Outdated verify results
    if len(verify_ids) > 1:
        logger.info("Found %d verify results, keeping only latest", len(verify_ids))
        for vid in verify_ids[:-1]:
            ids_to_remove.add(vid)
    else:
        logger.info("Found %d verify results, nothing to remove", len(verify_ids))

    logger.info(
        "Detected %d outdated tool IDs, tracking %d files",
        len(ids_to_remove),
        len(latest_file_positions),
    )
    return ids_to_remove, latest_file_positions

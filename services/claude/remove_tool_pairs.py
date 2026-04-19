from anthropic.types import MessageParam

from utils.logging.logging_config import logger


def remove_tool_pairs(messages: list[MessageParam], ids: set[str]):
    """Remove tool_use and tool_result blocks matching IDs, pop empty messages."""
    if not ids:
        logger.info("No outdated tool IDs to remove")
        return

    indices_to_pop: set[int] = set()

    for i, msg in enumerate(messages):
        content = msg.get("content")
        if not isinstance(content, list):
            logger.info("msg[%d]: skipping non-list content", i)
            continue

        new_content = []
        removed_from_msg = 0
        for item in content:
            if not isinstance(item, dict):
                new_content.append(item)
                continue

            tool_id = item.get("id")
            if (
                item.get("type") == "tool_use"
                and isinstance(tool_id, str)
                and tool_id in ids
            ):
                logger.info("Removing outdated tool_use %s", tool_id)
                removed_from_msg += 1
                continue

            use_id = item.get("tool_use_id")
            if (
                item.get("type") == "tool_result"
                and isinstance(use_id, str)
                and use_id in ids
            ):
                logger.info("Removing outdated tool_result for %s", use_id)
                removed_from_msg += 1
                continue

            new_content.append(item)

        if removed_from_msg == 0:
            logger.info("msg[%d]: no matching tool blocks", i)
            continue

        has_tool_block = any(
            isinstance(b, dict) and b.get("type") in ("tool_use", "tool_result")
            for b in new_content
        )
        if new_content and has_tool_block:
            logger.info(
                "msg[%d]: kept %d blocks, removed %d",
                i,
                len(new_content),
                removed_from_msg,
            )
            msg["content"] = new_content
        else:
            logger.info("msg[%d]: all tool blocks removed, popping", i)
            indices_to_pop.add(i)

    for i in sorted(indices_to_pop, reverse=True):
        messages.pop(i)

    logger.info(
        "Removed %d outdated tool pairs, popped %d empty messages",
        len(ids),
        len(indices_to_pop),
    )

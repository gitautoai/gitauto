from anthropic.types import MessageParam

from utils.logging.logging_config import logger


def remove_tool_pairs(messages: list[MessageParam], ids: set[str]):
    """Remove tool_use and tool_result blocks matching IDs, pop empty messages.

    Only the matching block is stripped. Any sibling `text` block in the same message survives — if a `text + tool_use` assistant message has its tool_use removed, the message keeps the text. The message is only popped when no content remains.

    Example, ids={"toolu_1"}:

    Before:
        [
          {"role": "assistant", "content": [
              {"type": "text", "text": "Plan: read the test file then append three describe blocks."},
              {"type": "tool_use", "id": "toolu_1", "name": "get_local_file_content",
               "input": {"file_path": "src/foo.test.ts"}},
          ]},
          {"role": "user", "content": [
              {"type": "tool_result", "tool_use_id": "toolu_1", "content": "...file content..."},
          ]},
        ]

    After:
        [
          {"role": "assistant", "content": [
              {"type": "text", "text": "Plan: read the test file then append three describe blocks."},
          ]},
        ]

    The user message is popped (empty after stripping its only tool_result).
    The assistant message is kept because the `text` block remains — the
    agent's plan stays in history.
    """
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
                logger.info("msg[%d]: keeping non-dict block as-is", i)
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

        if new_content:
            # Keep the message if anything remains, including text-only assistant messages after tool_use is stripped.
            # Popping the text loses the agent's plan and causes amnesia loops where it re-reads the same file.
            logger.info(
                "msg[%d]: kept %d blocks, removed %d",
                i,
                len(new_content),
                removed_from_msg,
            )
            msg["content"] = new_content
        else:
            logger.info("msg[%d]: all blocks removed, popping", i)
            indices_to_pop.add(i)

    for i in sorted(indices_to_pop, reverse=True):
        messages.pop(i)

    logger.info(
        "Removed %d outdated tool pairs, popped %d empty messages",
        len(ids),
        len(indices_to_pop),
    )

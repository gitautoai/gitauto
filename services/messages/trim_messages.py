from typing import Callable, Sequence

from anthropic.types import MessageParam

from services.messages.message_to_dict import message_to_dict
from utils.logging.logging_config import logger
from utils.objects.safe_get_attribute import safe_get_attribute


def trim_messages_to_token_limit(
    messages: Sequence[MessageParam],
    max_input: int,
    count_tokens_fn: Callable[[list[MessageParam]], int],
):
    """Drop oldest removable messages until count_tokens_fn(messages) <= max_input.

    Preserves the first user message and any system messages. Removes tool_use
    assistant messages together with their matching tool_result to keep the
    conversation structurally valid for any downstream SDK. count_tokens_fn is
    supplied by the caller so a single trim loop works for Claude (Anthropic
    count_tokens endpoint), Google (google-genai count_tokens on converted
    contents), or any other backend."""
    messages = list(messages)

    if not messages:
        logger.info("trim_messages_to_token_limit: empty messages, returning")
        return messages, 0

    token_input = count_tokens_fn(messages)
    logger.info(
        "trim_messages_to_token_limit: initial count=%d max=%d",
        token_input,
        max_input,
    )

    while token_input > max_input and len(messages) > 1:
        logger.info("trim: scanning %d messages for removable candidate", len(messages))
        for i, msg in enumerate(messages):
            msg_dict = message_to_dict(msg)
            role = safe_get_attribute(msg_dict, "role", "")

            if role == "system":
                logger.info("trim: msg[%d] role=system, skipping", i)
                continue

            if i == 0 and role == "user":
                logger.info("trim: msg[%d] first user, skipping", i)
                continue

            tool_use_id = None
            if role == "assistant" and i + 1 < len(messages):
                logger.info("trim: msg[%d] inspecting assistant content", i)
                content = safe_get_attribute(msg_dict, "content", [])
                if not isinstance(content, list):
                    logger.info(
                        "trim: msg[%d] assistant non-list content; removing single", i
                    )
                    del messages[i]
                    break

                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        logger.info("trim: msg[%d] found tool_use block", i)
                        tool_use_id = block.get("id")
                        break

            if not tool_use_id or i + 1 >= len(messages):
                logger.info("trim: msg[%d] no tool pair; removing single", i)
                del messages[i]
                break

            next_msg = message_to_dict(messages[i + 1])
            next_content = safe_get_attribute(next_msg, "content", [])

            if not isinstance(next_content, list):
                logger.info("trim: msg[%d] next content non-list; removing single", i)
                del messages[i]
                break

            has_matching_tool_result = False
            for block in next_content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and block.get("tool_use_id") == tool_use_id
                ):
                    logger.info("trim: msg[%d] matching tool_result found", i)
                    has_matching_tool_result = True
                    break

            if has_matching_tool_result:
                logger.info("trim: msg[%d] removing tool_use/result pair", i)
                del messages[i : i + 2]
            else:
                logger.info("trim: msg[%d] no matching result; removing single", i)
                del messages[i]
            break

        token_input = count_tokens_fn(messages)
        logger.info("trim: after removal len=%d tokens=%d", len(messages), token_input)

    logger.info(
        "trim_messages_to_token_limit: returning len=%d tokens=%d",
        len(messages),
        token_input,
    )
    return messages, token_input

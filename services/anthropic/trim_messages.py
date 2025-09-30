# Standard imports
from typing import Any

# Third party imports
from anthropic import Anthropic

# Local imports
from config import ANTHROPIC_MODEL_ID_45
from services.anthropic.message_to_dict import message_to_dict
from utils.objects.safe_get_attribute import safe_get_attribute


def trim_messages_to_token_limit(
    messages: list[Any],
    client: Anthropic,
    max_input: int,
    model: str = ANTHROPIC_MODEL_ID_45,
):
    messages = list(messages)  # Make a copy to avoid mutating the original

    # Early return if empty
    if not messages:
        return messages

    token_input = client.messages.count_tokens(
        messages=messages, model=model
    ).input_tokens

    # Keep removing messages from oldest (non-system) to newest until under limit
    while token_input > max_input and len(messages) > 1:
        # Find oldest non-system message that we can safely remove
        for i, msg in enumerate(messages):
            msg_dict = message_to_dict(msg)
            role = safe_get_attribute(msg_dict, "role", "")

            if role == "system":
                continue

            if i == 0 and role == "user":
                continue

            # Check if this is an assistant message with tool_use
            tool_use_id = None
            if role == "assistant" and i + 1 < len(messages):
                content = safe_get_attribute(msg_dict, "content", [])
                if not isinstance(content, list):
                    # Not a list, can safely remove
                    del messages[i]
                    break

                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_use_id = block.get("id")
                        break

            # If no tool_use_id, safe to remove this message
            if not tool_use_id or i + 1 >= len(messages):
                del messages[i]
                break

            # Check if next message has matching tool_result
            next_msg = message_to_dict(messages[i + 1])
            next_content = safe_get_attribute(next_msg, "content", [])

            if not isinstance(next_content, list):
                # Next message content not a list, remove current message only
                del messages[i]
                break

            has_matching_tool_result = False
            for block in next_content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and block.get("tool_use_id") == tool_use_id
                ):
                    has_matching_tool_result = True
                    break

            # If there's a matching tool_result, remove both messages together
            if has_matching_tool_result:
                del messages[i : i + 2]
            else:
                del messages[i]
            break

        # Recalculate token count after removal
        token_input = client.messages.count_tokens(
            messages=messages, model=model
        ).input_tokens

    return messages

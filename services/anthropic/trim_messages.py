# Standard imports
from typing import Any

# Third party imports
from anthropic import Anthropic
# Local imports
from config import ANTHROPIC_MODEL_ID_40
from services.anthropic.message_to_dict import message_to_dict
from utils.objects.safe_get_attribute import safe_get_attribute


def trim_messages_to_token_limit(
    messages: list[Any],
    client: Anthropic,
    max_input: int,
    model: str = ANTHROPIC_MODEL_ID_40,
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
            tool_use_ids = []
            if role == "assistant" and i + 1 < len(messages):
                content = safe_get_attribute(msg_dict, "content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_id = block.get("id")
                            if tool_id:  # Only add non-empty, non-None ids
                                tool_use_ids.append(tool_id)

            # If this message has tool_use blocks, check if ALL have matching tool_results
            if tool_use_ids and i + 1 < len(messages):
                next_msg = message_to_dict(messages[i + 1])
                next_content = safe_get_attribute(next_msg, "content", [])
                matched_tool_ids = set()

                # Collect all tool_result ids from next message
                if isinstance(next_content, list):
                    for block in next_content:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_result"
                        ):
                            result_id = block.get("tool_use_id")
                            if result_id:  # Only add non-empty, non-None ids
                                matched_tool_ids.add(result_id)

                # Check if ALL tool_use ids have matching tool_results
                all_tools_matched = all(tool_id in matched_tool_ids for tool_id in tool_use_ids)

                # If ALL tool_use blocks have matching tool_results, remove both messages together
                if all_tools_matched:
                    del messages[i : i + 2]
                    break

            # Regular message (no tool use) or no matching tool result found
            del messages[i]
            break

        # Recalculate token count after removal
        token_input = client.messages.count_tokens(
            messages=messages, model=model
        ).input_tokens

    return messages

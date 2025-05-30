# Standard imports
from typing import Any, cast

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

    token_input = cast(
        int,
        client.messages.count_tokens(messages=messages, model=model).input_tokens,
    )

    # Keep removing messages from oldest (non-system) to newest until under limit
    while token_input > max_input and len(messages) > 1:
        # Remove oldest non-system message
        for i, msg in enumerate(messages):
            msg_dict = message_to_dict(msg)
            role = safe_get_attribute(msg_dict, "role")
            if role != "system":
                del messages[i]
                break

        # Recalculate token count after removal
        token_input = cast(
            int,
            client.messages.count_tokens(messages=messages, model=model).input_tokens,
        )

    return messages

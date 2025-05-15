# Standard imports
from typing import Any, List, cast

# Third party imports
from anthropic import Anthropic

# Local imports
from services.anthropic.message_to_dict import message_to_dict
from utils.attribute.safe_get_attribute import safe_get_attribute


def trim_messages_to_token_limit(
    messages: List[Any], client: Anthropic, max_tokens: int = 200_000
):
    messages = list(messages)  # Make a copy to avoid mutating the original
    token_input = cast(
        int, client.messages.count_tokens(messages=messages).input_tokens
    )
    while token_input > max_tokens and len(messages) > 1:
        for i, msg in enumerate(messages):
            msg_dict = message_to_dict(msg)
            role = safe_get_attribute(msg_dict, "role")
            if role != "system":
                del messages[i]
                break
        token_input = cast(
            int, client.messages.count_tokens(messages=messages).input_tokens
        )
    return messages

# Standard imports
from typing import Any, cast

# Third party imports
from anthropic import Anthropic

# Local imports
from config import ANTHROPIC_MODEL_ID_37
from services.anthropic.message_to_dict import message_to_dict
from utils.attribute.safe_get_attribute import safe_get_attribute


def trim_messages_to_token_limit(
    messages: list[Any], client: Anthropic, model: str = ANTHROPIC_MODEL_ID_37
):
    messages = list(messages)  # Make a copy to avoid mutating the original
    token_input = cast(
        int,
        client.messages.count_tokens(messages=messages, model=model).input_tokens,
    )
    max_tokens = 200_000
    while token_input > max_tokens and len(messages) > 1:
        for i, msg in enumerate(messages):
            msg_dict = message_to_dict(msg)
            role = safe_get_attribute(msg_dict, "role")
            if role != "system":
                del messages[i]
                break
        token_input = cast(
            int,
            client.messages.count_tokens(messages=messages, model=model).input_tokens,
        )
    return messages

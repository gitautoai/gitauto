from typing import Any

from utils.attribute.safe_get_attribute import safe_get_attribute


def message_to_dict(message: Any) -> dict[str, Any]:
    """Convert a message object to a dictionary."""
    if isinstance(message, dict):
        return message

    result = {}
    for attr in ["role", "content", "tool_calls", "tool_call_id", "name"]:
        value = safe_get_attribute(message, attr)
        if value is not None:
            result[attr] = value
    return result

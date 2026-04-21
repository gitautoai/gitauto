from typing import Any

from utils.logging.logging_config import logger
from utils.objects.safe_get_attribute import safe_get_attribute


def message_to_dict(message: Any) -> dict[str, Any]:
    """Convert a message object to a dictionary."""
    if isinstance(message, dict):
        logger.info("message_to_dict: input already dict, returning as-is")
        return message

    result = {}
    for attr in ["role", "content", "tool_calls", "tool_use_id", "name"]:
        value = safe_get_attribute(message, attr, None)
        if value is not None:
            logger.info("message_to_dict: copied attr=%s", attr)
            result[attr] = value
    logger.info("message_to_dict: returning dict with %d keys", len(result))
    return result

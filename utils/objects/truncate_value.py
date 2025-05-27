from typing import Any


def truncate_value(value: Any, max_length: int = 30) -> Any:
    """Truncates string values in data structures to a maximum length.

    If a string's length exceeds max_length by 4 or more characters, it is truncated.
    The truncated string consists of the first (max_length - 4) characters followed by " ..." 
    or the first (max_length - 3) characters followed by "..." depending on the exact excess.
    Strings that are only marginally longer (excess < 4) are returned unchanged.
    For collections (dict, list, tuple), the function is applied recursively.
    Non-string values are returned unchanged.

    Args:
        value: The value to truncate, can be a string, dict, list, tuple, or any other type.
        max_length: The maximum length allowed for string values.

    Returns:
        The truncated value, with the same type as the input.
    """
    if isinstance(value, str):
        # Only truncate if the excess length is 4 or more
        if len(value) <= max_length or (len(value) - max_length) < 4:
            return value
        # If the excess is exactly 4, reserve 3 characters for ellipsis
        if (len(value) - max_length) == 4:
            return value[:max_length - 3] + "..."
        # Otherwise, reserve 4 characters for ' ...' so the result is exactly max_length
        return value[:max_length - 4] + " ..."
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    return value
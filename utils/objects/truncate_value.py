from typing import Any


def truncate_value(value: Any, max_length: int = 30) -> Any:
    """Truncates string values in data structures to a maximum length.

    If a string's length exceeds max_length by 4 or more characters, it is truncated.
    The truncated string consists of the first (max_length - 4) characters followed by " ...".
    Strings that are only marginally longer (excess < 4) are returned unchanged.
    For collections (dict, list, tuple), the function is applied recursively.
    Non-string values are returned unchanged.

    Args:
        value: The value to truncate. Can be a string, dict, list, tuple, or any other type.
        max_length: The maximum length allowed for string values. Defaults to 30.

    Returns:
        The truncated value. For strings that need truncation, returns a string of exactly
        max_length characters including the " ..." suffix. For collections, returns the same
        type with truncated string values. For other types, returns the value unchanged.
    """
    if isinstance(value, str):
        if len(value) <= max_length or (len(value) - max_length) < 4:
            return value
        return f"{value[:max_length-4]} ..."
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    return value
from typing import Any


def truncate_value(value: Any, max_length: int = 30):
    """Truncates string values in data structures to a maximum length.

    Args:
        value: The value to truncate. Can be a string, dict, list, tuple, or any other type.
        max_length: Maximum length for string values. Must be >= 0. Default is 30.

    Returns:
        - For strings: If length exceeds max_length by 4+ chars, returns first (max_length-4) chars + " ...".
                      Otherwise returns the original string unchanged.
        - For dicts/lists/tuples: Returns same type with values recursively truncated.
        - For other types: Returns the value unchanged.
    """
    if isinstance(value, str):
        if len(value) <= max_length or (len(value) - max_length) < 4:
            return value
        return f"{value[:max_length-3]}..."
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    return value

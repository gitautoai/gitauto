from typing import Any


def truncate_value(value: Any, max_length: int = 30) -> Any:
    """Truncates string values in data structures to a maximum length.

    Args:
        value: The value to truncate. Can be a string, dict, list, tuple or other type.
        max_length: Maximum length for string values before truncation.

    Returns:
        The value with any strings longer than max_length truncated.
        For strings that exceed max_length by 4 or more characters,
        truncates to (max_length - 4) and appends " ..." suffix.
        Strings that exceed max_length by less than 4 characters are not truncated.
    """
    # For strings, only truncate if longer than max_length
    if isinstance(value, str):
        # Only truncate if the excess length is 4 or more
        if len(value) <= max_length or (len(value) - max_length) < 4:
            return value
        # Reserve 4 characters for " ..." suffix
        return f"{value[:max_length-4]} ..."
    
    # Recursively process collections
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)

    # Return non-string values unchanged
    return value
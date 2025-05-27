from typing import Any


def truncate_value(value: Any, max_length: int = 30):
    """Truncate strings that are significantly longer than max_length.
    For strings that are only marginally longer than max_length, return them unchanged.
    For collections (dict, list, tuple), recursively process their contents.
    """
    if isinstance(value, str):
        # Only truncate if the excess length is 4 or more
        if len(value) <= max_length or (len(value) - max_length) < 4:
            return value
        # Simple truncation: reserve 3 characters for "..."
        return f"{value[:max_length-3]}..."
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    return value
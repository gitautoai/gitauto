from typing import Any


def truncate_value(value: Any, max_length: int = 30):
    if max_length < 0:
        max_length = 0
    if isinstance(value, str):
        if max_length == 0:
            return "..."
        elif len(value) > max_length:
            return f"{value[:max_length]}..."
        else:
            return value
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)
    return value


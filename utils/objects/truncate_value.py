from typing import Any


def truncate_value(value: Any, max_length: int = 30) -> Any:
    if isinstance(value, str) and len(value) > max_length:
        # Truncate by taking the first max_length characters and appending "..."
        return f"{value[:max_length]}..."
    if isinstance(value, dict):
        return {k: truncate_value(v, max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate_value(item, max_length) for item in value]
    if isinstance(value, tuple):
        return tuple(truncate_value(item, max_length) for item in value)

    return value

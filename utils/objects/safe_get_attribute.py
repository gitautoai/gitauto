from typing import Any, TypeVar

T = TypeVar("T")


def safe_get_attribute(obj: Any, attr: str, default: T):
    """Safely get an attribute from an object or dictionary."""
    if hasattr(obj, "get") and callable(obj.get):
        # Dictionary-like object
        return obj.get(attr, default)
    if hasattr(obj, attr):
        # Object with attributes
        return getattr(obj, attr, default)
    return default

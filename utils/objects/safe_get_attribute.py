def safe_get_attribute(obj: object, attr: str, default: object):
    """Safely get an attribute from an object or dictionary."""
    get_method = getattr(obj, "get", None)
    if get_method is not None and callable(get_method):
        return get_method(attr, default)
    if hasattr(obj, attr):
        return getattr(obj, attr, default)
    return default

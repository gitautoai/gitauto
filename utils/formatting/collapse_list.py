from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def collapse_list(items: list[str], max_items: int = 6):
    """Format a list for display, collapsing the middle if too long.

    Shows first half and last half of items, with count of omitted items in middle.
    Default max_items=6 means 3 items shown at start and 3 at end.
    """
    if not items:
        return ""
    if len(items) <= max_items:
        return "- " + "\n- ".join(items)

    half = max_items // 2
    first = items[:half]
    last = items[-half:]
    omitted = len(items) - max_items

    return (
        "- "
        + "\n- ".join(first)
        + f"\n- ... ({omitted} more items) ...\n- "
        + "\n- ".join(last)
    )

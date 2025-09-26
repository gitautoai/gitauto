import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda text: text, raise_on_error=False)
def remove_ansi_escape_codes(text: str):
    # Remove standard ANSI escape codes first (e.g., \x1b[31m, \x1b[2K)
    standard_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    text = standard_ansi.sub("", text)

    # Remove CircleCI-style bracket codes more carefully
    # Match specific patterns we know about
    patterns_to_remove = [
        r"\[2K",      # Clear line
        r"\[1G",      # Move cursor to column 1
        r"\[\d+G",    # Move cursor to column N
        r"\[\d*m",    # Color/style codes like [1m, [22m, [0m
        r"\[\d+;\d+m", # Complex color codes like [31;1m
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text)

    return text

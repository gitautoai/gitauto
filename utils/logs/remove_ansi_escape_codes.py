import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda text: text, raise_on_error=False)
def remove_ansi_escape_codes(text: str):
    # Remove standard ANSI escape codes first (e.g., \x1b[31m, \x1b[2K)
    standard_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    # Remove CircleCI-style bracket codes second (e.g., [2K, [1G)
    # Order matters: process standard format first to avoid conflicts
    bracket_ansi = re.compile(r"\[[0-9;]*[a-zA-Z]")
    text = standard_ansi.sub("", text)
    text = bracket_ansi.sub("", text)
    return text

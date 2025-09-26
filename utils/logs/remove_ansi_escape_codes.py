import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda text: text, raise_on_error=False)
def remove_ansi_escape_codes(text: str):
    # Remove standard ANSI escape codes first (e.g., \x1b[31m, \x1b[2K)
    standard_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    text = standard_ansi.sub("", text)

    # Remove CircleCI-style bracket codes (e.g., [2K, [1G, [1m, [22m)
    # Be more specific about what we match to avoid false positives
    bracket_ansi = re.compile(r"\[(?:\d+;?)*[a-zA-Z]")
    text = bracket_ansi.sub("", text)

    return text

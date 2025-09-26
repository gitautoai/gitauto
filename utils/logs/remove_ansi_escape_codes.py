import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda text: text, raise_on_error=False)
def remove_ansi_escape_codes(text: str):
    # Remove all ANSI escape sequences
    # This regex matches:
    # - \x1b[ followed by any characters until a letter (standard ANSI)
    # - [ followed by digits/semicolons and a letter (CircleCI style)
    ansi_escape = re.compile(r'(?:\x1b\[[0-9;]*[a-zA-Z]|\[[0-9;]*[a-zA-Z])')
    return ansi_escape.sub('', text)

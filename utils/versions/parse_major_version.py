import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def parse_major_version(text: str):
    """Extract major version from strings like 'v18.17.0', '18', 'lts/hydrogen', '22.1'."""
    text = text.lstrip("vV")

    # lts/* or lts/name — can't determine version
    if text.startswith("lts"):
        return None

    match = re.match(r"(\d+)", text)
    if match:
        return str(match.group(1))

    return None

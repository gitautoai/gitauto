import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def extract_max_major_from_constraint(constraint: str):
    """Extract the highest major version from a version constraint string.

    Examples:
        ">=18"              -> "18"
        "^18 || ^20"        -> "20"
        ">=16 <23"          -> "22"  (max mentioned is 23, but <23 means 22)
        "18.x"              -> "18"
        "^18 || ^20 || ^22" -> "22"
    """
    # Match version-like patterns (e.g. "18", "22.0.0", "20.10.0") and extract only
    # the leading major number. This skips minor/patch without hardcoding valid ranges.
    majors: list[int] = []
    for match in re.finditer(r"(\d+)(?:\.\d+)*", constraint):
        majors.append(int(match.group(1)))

    if not majors:
        return None

    # Exclusive upper bounds like "<23" — the usable version is one below
    max_major = max(majors)
    if re.search(rf"<\s*{max_major}(?!\d)", constraint):
        max_major -= 1

    return str(max_major)

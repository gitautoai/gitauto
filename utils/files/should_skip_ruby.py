import re


def should_skip_ruby(content: str) -> bool:
    """
    Determines if a Ruby file should be skipped for test generation.

    Returns True if the file contains only:
    - Require statements
    - Constants (UPPERCASE)
    - Autoload declarations

    Returns False if the file contains:
    - Method definitions
    - Class implementations with methods
    - Any executable code beyond declarations
    """
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        # Skip comments
        if line.startswith("#"):
            continue
        # Skip empty lines
        if not line:
            continue
        # Skip require statements
        if line.startswith("require ") or line.startswith("require_relative "):
            continue
        # Skip autoload
        if line.startswith("autoload "):
            continue
        # Skip constants (Ruby constants are UPPERCASE)
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", line):
            continue
        # If we find any other code, it's not export-only
        return False

    return True

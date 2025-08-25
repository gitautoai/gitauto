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
    in_empty_class = False
    in_heredoc = False

    for line in lines:
        line = line.strip()

        # Handle heredoc strings (<<~TEXT ... TEXT)
        if not in_heredoc and "<<" in line:
            in_heredoc = True
            continue
        if in_heredoc:
            # Check if we've reached the end marker
            if line and not line.startswith(" ") and line.isalpha():
                in_heredoc = False
            continue

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
        # Handle empty class/module definitions
        if line.startswith("class ") or line.startswith("module "):
            in_empty_class = True
            continue
        if in_empty_class and line == "end":
            in_empty_class = False
            continue
        if in_empty_class:
            # Skip attr_accessor, attr_reader, attr_writer in modules/classes
            if line.startswith("attr_"):
                continue
            # If there's any other content inside the class/module, it's not empty
            return False
        # If we find any other code, it's not export-only
        return False

    return True

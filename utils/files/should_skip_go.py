import re


def should_skip_go(content: str) -> bool:
    """
    Determines if a Go file should be skipped for test generation.

    Returns True if the file contains only:
    - Package declarations
    - Import statements
    - Constants and variables
    - Type definitions (struct, interface without methods)
    - Type aliases

    Returns False if the file contains:
    - Function definitions (func)
    - Method definitions (func with receiver)
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_struct = False
    in_interface = False
    in_multiline_string = False
    in_multiline_comment = False

    for line in lines:
        line = line.strip()
        # Skip comments
        if line.startswith("//"):
            continue
        # Handle multiline comments
        if "/*" in line and not in_multiline_comment:
            in_multiline_comment = True
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue
        # Handle multiline string literals (backticks)
        if not in_multiline_string and "const " in line and "`" in line:
            if line.count("`") == 1:  # String starts
                in_multiline_string = True
                continue
        if in_multiline_string:
            if "`" in line:  # String ends
                in_multiline_string = False
            continue
        # Skip empty lines
        if not line:
            continue
        # Skip package declaration
        if line.startswith("package "):
            continue

        # Handle struct definitions (data types without methods)
        if line.startswith("type ") and "struct" in line:
            if "{" in line:
                in_struct = True
            continue
        # Handle interface definitions
        if line.startswith("type ") and "interface" in line:
            if "{" in line:
                in_interface = True
            continue
        if in_struct or in_interface:
            if "}" in line:
                in_struct = False
                in_interface = False
            continue

        # Skip type aliases
        if re.match(r"^type\s+\w+\s+", line) and "=" not in line:
            continue

        # Skip import statements
        if line.startswith("import ") or line == "import (" or line == ")":
            continue
        # Skip individual imports in import block
        if line.startswith('"') and line.endswith('"'):
            continue
        # Skip constants (Go const are truly constant - compile-time immutable values)
        if (
            line.startswith("const ")
            or line == "const ("
            or line.startswith("var ")
            or line == "var ("
        ):
            # But NOT if they contain function calls
            if "(" in line and ")" in line and not line.endswith("("):
                return False
            continue
        # Skip individual const/var declarations in blocks - but NOT if they contain function calls
        if re.match(r"^\w+(\s+\w+)?\s*=", line):
            if "(" in line and ")" in line:  # Contains function calls
                return False
            continue
        # Skip bare const declarations without assignment (like StatusInactive)
        if re.match(r"^\w+$", line):
            continue
        # Skip field definitions in structs (name Type format)
        if re.match(r"^\w+\s+[\w\[\]\*\.]+$", line):
            continue
        # If we find any other code, it's not export-only
        return False

    return True

import re


def should_skip_python(content: str) -> bool:
    """
    Determines if a Python file should be skipped for test generation.

    Returns True if the file contains only:
    - Import/export statements
    - Constants and literals (including multi-line strings)
    - TypedDict or NamedTuple class definitions
    - Simple exception classes with only docstrings
    - __all__ definitions

    Returns False if the file contains:
    - Function definitions with logic
    - Class implementations with methods
    - Any executable code beyond declarations
    """
    lines = content.split("\n")

    # State tracking for multi-line constructs
    in_multiline_import = False
    in_multiline_string = False
    in_multiline_list = False
    in_class_definition = False
    in_exception_class = False
    in_triple_quote_string = False
    triple_quote_type = None

    for line in lines:
        line = line.strip()

        # Handle triple-quoted strings (including multi-line string constants)
        if not in_triple_quote_string:
            if '"""' in line or "'''" in line:
                # Check if this is a string assignment (constant)
                if re.match(r'^[A-Z_][A-Z0-9_]*\s*=\s*["\']', line):
                    # This is a string constant assignment
                    triple_quote_type = '"""' if '"""' in line else "'''"
                    # Check if string closes on same line
                    if line.count(triple_quote_type) >= 2:
                        # String opens and closes on same line
                        continue
                    # String continues to next lines
                    in_triple_quote_string = True
                    continue
        else:
            # We're inside a multi-line string constant
            if triple_quote_type in line:
                # String ends
                in_triple_quote_string = False
                triple_quote_type = None
            continue

        # Skip comments
        if line.startswith("#"):
            continue
        # Skip empty lines
        if not line:
            continue

        # Handle TypedDict class definitions
        if re.match(r"^class\s+\w+\(TypedDict\):", line):
            in_class_definition = True
            continue

        # Handle simple exception class definitions
        if re.match(r"^class\s+\w+\((Exception|Error|Warning)\):", line):
            in_exception_class = True
            continue

        # Handle other data classes (NamedTuple, dataclass, etc.)
        if re.match(r"^class\s+\w+\((NamedTuple|typing\.NamedTuple)\):", line):
            in_class_definition = True
            continue

        # If we're in a simple class definition, skip type annotations and docstrings
        if in_class_definition or in_exception_class:
            # Type annotations in TypedDict/NamedTuple
            if re.match(r"^\w+:\s+", line):
                continue
            # Docstrings in exception classes
            if (
                line.startswith('"""')
                or line.startswith("'''")
                or re.match(r'^".*"$', line)
            ):
                continue
            # Empty pass statement
            if line == "pass":
                continue
            # Check if class definition ends (non-indented line that's not part of class)
            if not line.startswith(" ") and not line.startswith("\t"):
                in_class_definition = False
                in_exception_class = False
                # Re-process this line as it's outside the class
                # But first check if it's another class definition
                if re.match(r"^class\s+", line):
                    if re.match(r"^class\s+\w+\(TypedDict\):", line):
                        in_class_definition = True
                        continue
                    if re.match(r"^class\s+\w+\((Exception|Error|Warning)\):", line):
                        in_exception_class = True
                        continue
                    if re.match(
                        r"^class\s+\w+\((NamedTuple|typing\.NamedTuple)\):", line
                    ):
                        in_class_definition = True
                        continue
                    # Other class definitions are considered logic
                    return False
            continue

        # Handle multi-line imports
        if line.startswith("from ") and "(" in line:
            in_multiline_import = True
            continue
        if in_multiline_import:
            if ")" in line:
                in_multiline_import = False
            continue

        # Skip import statements
        if line.startswith("import ") or line.startswith("from "):
            continue
        # Skip __all__ definition
        if line.startswith("__all__") or "__all__" in line and "=" in line:
            continue

        # Handle multi-line string assignments
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=\s*\(", line):
            in_multiline_string = True
            continue
        if in_multiline_string:
            if line == ")":
                in_multiline_string = False
            continue

        # Handle multi-line list assignments
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=\s*\[", line):
            in_multiline_list = True
            continue
        if in_multiline_list:
            if line == "]":
                in_multiline_list = False
            continue

        # Skip ALL variable assignments that are just data (no function calls or logic)
        # Allow list concatenation with * operator but exclude function calls
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=\s*", line) and not re.search(
            r"[a-z_]+\(", line
        ):
            continue
        # Skip any assignments with literals (but not function calls)
        if re.match(
            r"^\w+\s*=\s*[\(\[\{\"'`\d\-\+fTrueFalseNone\*]", line
        ) and not re.search(r"[a-z_]+\(", line):
            continue

        # Skip bare strings (continuation of multi-line strings)
        if re.match(r'^".*"$', line):
            continue

        # If we find any other code, it's not export-only
        return False

    return True

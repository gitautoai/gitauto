import re


def should_skip_php(content: str) -> bool:
    """
    Determines if a PHP file should be skipped for test generation.

    Returns True if the file contains only:
    - Include/require statements
    - Use statements and namespace declarations
    - Constants (const, define)
    - Interface/trait definitions without implementation
    - Simple class definitions (data classes)

    Returns False if the file contains:
    - Function definitions with logic
    - Method implementations
    - Class implementations with methods
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_multiline_comment = False
    in_interface = False
    in_trait = False
    in_class = False
    in_array_initialization = False
    in_heredoc = False
    expecting_brace_for_interface = False
    expecting_brace_for_trait = False
    expecting_brace_for_class = False

    for line in lines:
        line = line.strip()

        # Handle heredoc strings (<<<EOT ... EOT;)
        if not in_heredoc and "<<<" in line:
            in_heredoc = True
            continue
        if in_heredoc:
            if line.endswith(";") and not line.startswith("<<<"):
                in_heredoc = False
            continue

        # Handle multi-line comments
        if "/*" in line:
            in_multiline_comment = True
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue

        # Skip single-line comments
        if line.startswith("//") or line.startswith("#"):
            continue
        # Skip PHP tags
        if line in ["<?php", "<?", "?>"]:
            continue
        # Skip empty lines
        if not line:
            continue

        # Handle standalone opening brace for interface/trait/class
        if re.match(r"^\{", line):
            if expecting_brace_for_interface:
                in_interface = True
                expecting_brace_for_interface = False
            elif expecting_brace_for_trait:
                in_trait = True
                expecting_brace_for_trait = False
            elif expecting_brace_for_class:
                in_class = True
                expecting_brace_for_class = False
            continue

        # Handle interface definitions (no implementation)
        if re.match(r"^(abstract\s+|final\s+)?interface\s+\w+", line):
            if "{" in line:
                in_interface = True
            else:
                expecting_brace_for_interface = True
            continue
        if in_interface:
            if "}" in line:
                in_interface = False
                continue
            # Skip method signatures in interfaces
            if re.match(
                r"^\s*(public\s+|private\s+|protected\s+)?function\s+\w+\s*\(.*\)\s*;",
                line,
            ):
                continue
            continue

        # Handle trait definitions (mixins without implementation)
        if re.match(r"^trait\s+\w+", line):
            if "{" in line:
                in_trait = True
            else:
                expecting_brace_for_trait = True
            continue
        if in_trait:
            if "}" in line:
                in_trait = False
            continue

        # Handle simple class definitions (data classes, DTOs)
        if re.match(r"^(abstract\s+|final\s+)?class\s+\w+", line):
            if "{" in line:
                in_class = True
            else:
                expecting_brace_for_class = True
            continue
        if in_class:
            if "}" in line:
                in_class = False
                continue
            # Check for function definitions inside class BEFORE skipping
            if re.match(
                r"^\s*(public\s+|private\s+|protected\s+)?function\s+\w+", line
            ):
                return False
            # Skip property declarations
            if re.match(
                r"^\s*(public\s+|private\s+|protected\s+)?\s*\$\w+", line
            ):
                continue
            # Skip property declarations with type hints
            if re.match(
                r"^\s*(public\s+|private\s+|protected\s+)?\s*\w+\s+\$\w+", line
            ):
                continue
            # Skip const declarations inside class
            if re.match(r"^\s*const\s+\w+", line):
                continue
            continue

        # Skip namespace declarations
        if re.match(r"^namespace\s+[\w\\]+\s*;", line):
            continue
        # Skip use statements
        if re.match(r"^use\s+[\w\\]+", line):
            continue
        # Skip include/require statements
        if re.match(r"^(include|require)(_once)?\s*\(", line):
            continue
        if re.match(r"^(include|require)(_once)?\s+['\"]", line):
            continue
        # Skip const declarations
        if re.match(r"^const\s+\w+", line):
            continue
        # Skip define() calls
        if re.match(r"^define\s*\(", line):
            continue

        # Handle array initialization
        if re.match(r"^\$\w+\s*=\s*\[", line):
            in_array_initialization = True
            continue
        if in_array_initialization:
            if "];" in line:
                in_array_initialization = False
            continue

        # Skip variable assignments with string literals
        if re.match(r"^\$\w+\s*=\s*['\"]", line):
            continue
        # Skip return statements with string literals
        if re.match(r"^return\s+['\"]", line):
            continue
        # Skip closing parenthesis with semicolon (end of function calls)
        if re.match(r"^\)\s*;", line):
            continue

        # If we reach here, there's executable code
        return False

    return True

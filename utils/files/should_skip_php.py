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
    pending_class = False

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

        # Handle interface definitions (no implementation)
        if re.match(r"^(abstract\s+|final\s+)?interface\s+\w+", line):
        if re.match(r"^\{", line):
            continue
            in_interface = True
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
                pending_class = True
            continue
        if pending_class and re.match(r"^\{", line):
            in_class = True
            pending_class = False
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
            # Skip property declarations in classes
            if re.match(r"^\s*(public\s+|private\s+|protected\s+)?\$\w+", line):
                continue
            continue

        # Skip require/include statements
        if any(
            line.startswith(x)
            for x in [
                "require ",
                "require_once ",
                "include ",
                "include_once ",
                "use ",
            ]
        ):
            continue
        # Skip namespace declaration
        if line.startswith("namespace "):
            continue
        # Skip constants (comprehensive pattern)
        if re.match(
            r"^(public\s+|private\s+|protected\s+)?(const\s+[A-Z_][A-Z0-9_]*\s*=|define\s*\()",
            line,
        ):
            continue
        # Skip global constants (any case for PHP)
        if re.match(r"^const\s+\w+\s*=", line):
            continue
        # Skip simple variable assignments (configuration arrays, etc.)
        if re.match(r"^\$\w+\s*=\s*[\[\{\"']", line):
            if "[" in line and "]" not in line:
                in_array_initialization = True
            continue
        # Skip return statements with simple values (for config files)
        if re.match(r"^return\s+[\[\{\"']", line):
            if "[" in line and "]" not in line:
                in_array_initialization = True
            continue
        # Handle multi-line array initializations
        if in_array_initialization:
            if "]" in line or "};" in line:
                in_array_initialization = False
            continue
        # Skip array elements in multi-line arrays (values)
        if re.match(r"^\s*['\"]?\w+['\"]?\s*=>\s*['\"]?[\w\-\.]+['\"]?,?\s*$", line):
            continue
        # Skip nested array elements (array as value)
        if re.match(r"^\s*['\"]?\w+['\"]?\s*=>\s*\[", line):
            continue
        # Skip array closing with comma
        if re.match(r"^\s*\],?\s*$", line):
            continue
        # Skip closing statements
        if line in ["}", "];", ");", "?>"]:
            continue

        # If we find function definitions or other logic, don't skip
        if re.match(r"^(public\s+|private\s+|protected\s+)?function\s+\w+", line):
            return False
        if (
            line.startswith("if ")
            or line.startswith("for ")
            or line.startswith("while ")
        ):
            return False

        # If we find any other code, it's not export-only
        return False

    return True

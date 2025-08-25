import re


def should_skip_csharp(content: str) -> bool:
    """
    Determines if a C#/VB.NET/F# file should be skipped for test generation.

    Returns True if the file contains only:
    - Using/import statements
    - Namespace declarations
    - Constants
    - Interface definitions without implementation
    - Record definitions (C# 9.0+ immutable data types)
    - Struct definitions (value types without methods)
    - Enum definitions
    - Attribute definitions

    Returns False if the file contains:
    - Method implementations
    - Class implementations with logic
    - Property implementations with logic
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_multiline_comment = False
    in_interface = False
    in_struct = False
    in_enum = False
    in_attribute = False
    in_record = False
    in_const_initialization = False
    in_multiline_string = False

    for line in lines:
        line = line.strip()

        # Handle verbatim strings (@"...")
        if not in_multiline_string and '@"' in line:
            if line.count('"') == 1:  # String starts
                in_multiline_string = True
                continue
        if in_multiline_string:
            if '";' in line:
                in_multiline_string = False
            continue

        # Handle multi-line comments
        if "/*" in line:
            in_multiline_comment = True
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue

        # Skip single-line comments
        if line.startswith("//") or line.startswith("'"):
            continue
        # Skip empty lines
        if not line:
            continue

        # Handle interface definitions
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?(partial\s+)?interface\s+\w+",
            line,
        ):
            in_interface = True
            continue
        if re.match(r"^\{", line):
            continue
        if in_interface:
            if "}" in line:
                in_interface = False
                continue
            # Skip property and method signatures in interfaces
            if re.match(r"^\s*\w+\s+\w+\s*{\s*(get;\s*set;|get;)\s*}", line):
                continue
            if re.match(r"^\s*\w+\s+\w+\s*\(.*\)\s*;", line):
                continue
            continue

        # Handle struct definitions (value types)
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?(readonly\s+)?struct\s+\w+",
            line,
        ):
            if "{" in line:
                in_struct = True
            continue
        if in_struct:
            if "}" in line:
                in_struct = False
            # Skip field declarations in structs
            if re.match(
                r"^\s*(public\s+|private\s+|internal\s+|protected\s+)?\w+\s+\w+\s*;",
                line,
            ):
                continue
            continue

        # Handle enum definitions
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?enum\s+\w+", line
        ):
            if "{" in line:
                in_enum = True
            continue
        if in_enum:
            if "}" in line:
                in_enum = False
            # Skip enum members
            if re.match(r"^\s*\w+\s*(=\s*\d+)?\s*,?", line):
                continue
            continue

        # Handle record definitions (C# 9.0+ immutable data types)
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?record\s+\w+", line
        ):
            if "{" in line or ";" in line:
                in_record = True
            continue

        # Handle simple empty class definitions
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?class\s+\w+(\s*:\s*[^{]+)?\s*$",
            line,
        ) or re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?class\s+\w+(\s*:\s*[^{]+)?\s*\{",
            line,
        ):
            in_struct = True  # Reuse struct logic for empty classes
            continue
        if in_record:
            if "}" in line or line.endswith(";"):
                in_record = False
            # Skip record properties
            if re.match(r"^\s*\w+\s+\w+\s*{\s*get;\s*(init;|set;)?\s*}", line):
                continue
            continue

        # Handle attribute definitions
        if re.match(r"^\[.*Attribute.*\]", line):
            in_attribute = True
            continue
        if in_attribute:
            if re.match(r"^(public\s+|internal\s+)?class\s+\w+Attribute", line):
                in_attribute = False
            continue

        # Skip using statements (C#/F#)
        if line.startswith("using ") or line.startswith("open "):
            continue
        # Skip imports (VB.NET)
        if line.startswith("Imports "):
            continue
        # Skip namespace declaration
        if line.startswith("namespace "):
            continue
        # Skip module declaration (F#)
        if line.startswith("module "):
            continue
        # Skip assembly attributes
        if line.startswith("[assembly:"):
            continue
        # Skip global using (C# 10.0+)
        if line.startswith("global using "):
            continue

        # Skip constants (comprehensive pattern)
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+)?(readonly\s+)?const\s+\w+\s+\w+\s*=",
            line,
        ):
            if "{" in line and "}" not in line:
                in_const_initialization = True
            continue
        # Skip static readonly fields (effectively constants) - updated to handle generics
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?static\s+readonly\s+[\w\<\>\[\],\s]+\s+[A-Z_][A-Z0-9_]*\s*=",
            line,
        ):
            if "{" in line and "}" not in line:
                in_const_initialization = True
            continue
        # Handle multi-line constant initializations
        if in_const_initialization:
            if "}" in line:
                in_const_initialization = False
            continue
        # Skip dictionary/array initializations (simple data)
        if re.match(r"^\s*\[.*\]\s*=\s*\d+,?", line):
            continue
        # Skip F# let bindings for constants
        if re.match(r"^let\s+[A-Z_][A-Z0-9_]*\s*=\s*[\"'0-9\[]", line):
            continue
        # Skip simple property declarations with auto-getters/setters
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?\w+\s+\w+\s*{\s*(get;\s*set;|get;\s*init;|get;)\s*}",
            line,
        ):
            continue

        # Skip closing braces and semicolons
        if line in ["}", "};", ";", "]"]:
            continue

        # If we find method definitions or other logic, don't skip
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+|virtual\s+|override\s+|abstract\s+)?\w+\s+\w+\s*\(.*\)\s*{",
            line,
        ):
            return False
        if (
            line.startswith("if ")
            or line.startswith("for ")
            or line.startswith("while ")
            or line.startswith("foreach ")
        ):
            return False
        if line.startswith("return ") and not re.match(r"^return\s+[\[\{\"'0-9]", line):
            return False

        # If we find any other code, it's not export-only
        return False

    return True

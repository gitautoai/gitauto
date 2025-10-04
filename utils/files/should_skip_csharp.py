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

        # Skip single-line comments and empty lines
        if line.startswith("//") or line.startswith("'") or not line:
            continue

        # Skip using statements, imports, namespace declarations
        import_prefixes = (
            "using ",
            "open ",
            "Imports ",
            "namespace ",
            "module ",
            "global using ",
        )
        if any(line.startswith(prefix) for prefix in import_prefixes):
            continue

        # Skip assembly attributes
        if line.startswith("[assembly:"):
            continue

        # Skip constants - these are declarations only
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+)?(readonly\s+)?const\s+",
            line,
        ):
            continue

        # Static readonly with function calls (has logic) - must check BEFORE skipping static readonly
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?static\s+readonly\s+",
            line,
        ) and ("(" in line and ")" in line):
            return False

        # Skip static readonly fields that are effectively constants (no function calls)
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?static\s+readonly\s+",
            line,
        ):
            continue

        # Skip simple property declarations (auto-properties are just data, no logic to test)
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?\w+\s+\w+\s*{\s*get;\s*((private\s+|protected\s+|internal\s+)?set;|(private\s+|protected\s+|internal\s+)?init;)?\s*}",
            line,
        ):
            continue

        # Skip record definitions (immutable data types, no logic)
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?record\s+\w+", line
        ):
            continue

        # Skip enum definitions - enums are just constants
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?enum\s+\w+", line
        ):
            continue

        # Skip interface definitions without implementations
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?(partial\s+)?interface\s+\w+",
            line,
        ):
            continue

        # Skip empty class/struct definitions (single line)
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?(abstract\s+|sealed\s+)?(class|struct)\s+\w+.*{\s*}",
            line,
        ):
            continue

        # Skip class/struct definitions (declaration only - content will be processed)
        if re.match(
            r"^(public\s+|internal\s+|private\s+|protected\s+)?(abstract\s+|sealed\s+)?(class|struct)\s+\w+.*[^{]$",
            line,
        ):
            continue

        # Skip simple closing braces, semicolons
        if line in ["}", "};", ";", "]", "{"]:
            continue

        # Skip field declarations in classes/structs (just data) - but NOT if they have function calls
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+)?(readonly\s+)?\w+\s+\w+(\s*=.*)?;?\s*$",
            line,
        ) and not ("(" in line and ")" in line):
            continue

        # Skip enum member declarations (just constants)
        if re.match(r"^\w+\s*(=\s*\d+)?\s*,?\s*$", line):
            continue

        # Skip interface method signatures (just contracts, no implementations)
        # These typically have return type + method name pattern like "void DoSomething();" or "Task<User> GetUserAsync(int id);"
        if re.match(
            r"^(public\s+|private\s+|protected\s+|internal\s+)?[\w<>]+\s+\w+\s*\(.*\)\s*;$",
            line,
        ):
            continue

        # IF WE FIND ANY OF THESE, THE FILE HAS LOGIC AND SHOULD BE TESTED:

        # Method definitions with implementations
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+|virtual\s+|override\s+|abstract\s+)?\w+\s+\w+\s*\(.*\)\s*{",
            line,
        ):
            return False

        # Constructor definitions
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?\w+\s*\(.*\)\s*{", line
        ):
            return False

        # Method signatures without braces (multi-line method definitions)
        if re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+|virtual\s+|override\s+|abstract\s+)?\w+\s+\w+\s*\(.*\)\s*$",
            line,
        ):
            return False

        # Control flow statements
        control_flow_prefixes = ("if ", "for ", "while ", "foreach ", "switch ", "try ")
        if any(line.startswith(prefix) for prefix in control_flow_prefixes):
            return False

        # Return statements with logic
        if line.startswith("return ") and not re.match(r"^return\s+[\[{\"'0-9]", line):
            return False

        # Variable assignments (not constant declarations)
        if "=" in line and not re.match(
            r"^(public\s+|private\s+|internal\s+|protected\s+)?(static\s+)?(readonly\s+)?const\s+",
            line,
        ):
            return False

        # Method calls
        if re.match(r"^\w+\s*\(.*\)\s*;?$", line):
            return False

        # Any other executable code
        if line and not line.startswith("#") and not line.startswith("//"):
            return False

    return True

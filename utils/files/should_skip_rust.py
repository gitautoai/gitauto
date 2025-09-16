import re


def should_skip_rust(content: str) -> bool:
    """
    Determines if a Rust file should be skipped for test generation.

    Returns True if the file contains only:
    - Use statements and mod declarations
    - Constants (const and static)
    - Type definitions (struct, enum, trait without implementation)
    - Type aliases

    Returns False if the file contains:
    - Function definitions (fn)
    - Implementation blocks (impl)
    - Macros with logic
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_struct_or_enum = False
    in_trait = False
    in_multiline_string = False
    multiline_comment_depth = 0

    for line in lines:
        line = line.strip()

        # Handle multiline comments (/* ... */)
        # Count opening and closing comment markers
        multiline_comment_depth += line.count("/*")
        multiline_comment_depth -= line.count("*/")
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue

        # Handle multiline raw strings (r#"..."#)
        if not in_multiline_string and 'r#"' in line and not (line.endswith('"#;') or line.endswith('"#')):
            in_multiline_string = True
            continue
        if in_multiline_string:
            if line.endswith('"#;') or line.endswith('"#'):
                in_multiline_string = False
            continue

        # Skip comments
        if line.startswith("//") or (line.startswith("/*") and line.endswith("*/")):
            continue
        # Skip attributes
        if line.startswith("#[") or line.startswith("#!["):
            continue
        # Skip empty lines
        if not line:
            continue

        # Handle struct/enum definitions (data types without implementation)
        if re.match(r"^(pub\s+)?struct\s+\w+", line):
            if "{" in line:
                # Only set flag if struct is not complete on same line
                if "}" not in line:
                    in_struct_or_enum = True
            elif not line.endswith(";"):
                # Opening brace might be on next line
                in_struct_or_enum = True
            continue
        if re.match(r"^(pub\s+)?enum\s+\w+", line):
            if "{" in line:
                # Only set flag if enum is not complete on same line
                if "}" not in line:
                    in_struct_or_enum = True
            elif not line.endswith(";"):
                # Opening brace might be on next line
                in_struct_or_enum = True
            continue
        if in_struct_or_enum:
            if line == "{":
                continue  # Just the opening brace on its own line
            if "}" in line:
                in_struct_or_enum = False
            continue

        # Handle trait definitions (interfaces without implementation)
        if re.match(r"^(pub\s+)?trait\s+\w+", line):
            if "{" in line:
                # Only set flag if trait is not complete on same line
                if "}" not in line:
                    in_trait = True
            elif not line.endswith(";"):
                # Opening brace might be on next line
                in_trait = True
            continue
        if in_trait:
            if line == "{":
                continue  # Just the opening brace on its own line
            if "}" in line:
                in_trait = False
            continue

        # Skip type aliases
        if re.match(r"^(pub\s+)?type\s+\w+\s*=", line):
            continue

        # Skip use statements
        if line.startswith("pub use ") or line.startswith("use "):
            continue
        # Skip mod statements
        if line.startswith("pub mod ") or line.startswith("mod "):
            continue
        # Skip extern crate
        if line.startswith("extern crate"):
            continue
        # Skip constants (Rust const is truly constant - compile-time immutable values)
        if line.startswith("pub const ") or line.startswith("const "):
            # Check if constant has function calls (like env::var() or Path::new())
            # Function calls are indicated by :: followed by parentheses
            if "::" in line and ("(" in line and ")" in line):
                return False
            # Check for array indexing which is runtime behavior (variable[index])
            if re.search(r"\w+\[", line):
                return False
            continue
        # Skip static variables (global variables with 'static lifetime)
        if line.startswith("pub static ") or line.startswith("static "):
            # Check if static has function calls (like env::var() or Path::new())
            # Function calls are indicated by :: followed by parentheses
            if "::" in line and ("(" in line and ")" in line):
                return False
            # Check for array indexing which is runtime behavior (variable[index])
            if re.search(r"\w+\[", line):
                return False
            continue
        # If we find any other code, it's not export-only
        return False

    return True

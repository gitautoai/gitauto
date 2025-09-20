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
    struct_enum_brace_depth = 0
    trait_brace_depth = 0
    in_multiline_string = False
    in_multiline_comment = False
    expecting_struct_enum_brace = False
    expecting_trait_brace = False

    for line in lines:
        line = line.strip()

        # Handle multiline comments (/* ... */)
        if not in_multiline_comment and "/*" in line and "*/" not in line:
            in_multiline_comment = True
            continue
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue

        # Handle multiline raw strings (r#"..."#)
        if not in_multiline_string and 'r#"' in line and not line.endswith('"#;'):
            in_multiline_string = True
            continue
        if in_multiline_string:
            if line.endswith('"#;'):
                in_multiline_string = False
            continue

        # Skip comments
        if line.startswith("//"):
            continue
        # Handle inline multiline comments /* ... */ on same line
        if line.startswith("/*") and "*/" in line:
            # Extract code after the comment
            comment_end = line.find("*/") + 2
            line = line[comment_end:].strip()
            if not line:
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
                struct_enum_brace_depth = 1
            else:
                expecting_struct_enum_brace = True
            continue
        if re.match(r"^(pub\s+)?enum\s+\w+", line):
            if "{" in line:
                struct_enum_brace_depth = 1
            else:
                expecting_struct_enum_brace = True
            continue
        if expecting_struct_enum_brace and line == "{":
            struct_enum_brace_depth = 1
            expecting_struct_enum_brace = False
            continue
        if struct_enum_brace_depth > 0:
            # Count opening and closing braces
            struct_enum_brace_depth += line.count("{") - line.count("}")
            continue

        # Handle trait definitions (interfaces without implementation)
        if re.match(r"^(pub\s+)?trait\s+\w+", line):
            if "{" in line:
                trait_brace_depth = 1
            else:
                expecting_trait_brace = True
            continue
        if expecting_trait_brace and line == "{":
            trait_brace_depth = 1
            expecting_trait_brace = False
            continue
        if trait_brace_depth > 0:
            # Count opening and closing braces
            trait_brace_depth += line.count("{") - line.count("}")
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
            # Check if constant has function calls (like env::var() or Path::new()) but not struct constructors
            if (
                "::" in line
                and ("(" in line and ")" in line)
                and not re.search(r"\w+\s*\{\}", line)
            ):
                return False
            # Check for array indexing which is runtime behavior (variable[index])
            if re.search(r"\w+\[", line):
                return False
            continue
        # Skip static variables (global variables with 'static lifetime)
        if line.startswith("pub static ") or line.startswith("static "):
            # Check if static has function calls (like env::var() or Path::new()) but not struct constructors
            if (
                "::" in line
                and ("(" in line and ")" in line)
                and not re.search(r"\w+\s*\{\}", line)
            ):
                return False
            # Check for array indexing which is runtime behavior (variable[index])
            if re.search(r"\w+\[", line):
                return False
            continue
        # Skip impl blocks (implementation blocks contain executable code)
        if re.match(r"^(pub\s+)?impl\s+", line):
            return False
        # Skip function definitions (executable code)
        if re.match(r"^(pub\s+)?fn\s+", line):
            return False
        # If we find any other code, it's not export-only
        return False

    return True

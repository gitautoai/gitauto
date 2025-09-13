import re


def should_skip_cpp(content: str) -> bool:
    """
    Determines if a C/C++ file should be skipped for test generation.

    Returns True if the file contains only:
    - Preprocessor directives (#include, #define, etc.)
    - Forward declarations
    - Struct/class/enum declarations without implementation
    - Constants and extern declarations
    - Using statements and namespaces

    Returns False if the file contains:
    - Function implementations
    - Method implementations
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_struct_or_class = False
    in_enum = False
    in_namespace = False
    in_raw_string = False
    in_multiline_comment = False
    in_typedef = False
    typedef_brace_count = 0

    for line in lines:
        line = line.strip()

        # Handle raw string literals (C++11 R"(...)")
        if not in_raw_string and 'R"(' in line:
            in_raw_string = True
            continue
        if in_raw_string:
            if ')";' in line:
                in_raw_string = False
            continue

        # Handle multiline comments
        if not in_multiline_comment and "/*" in line:
            in_multiline_comment = True
            continue
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue

        # Skip single-line comments
        if line.startswith("//"):
            continue
        # Skip preprocessor directives
        if line.startswith("#"):
            continue
        # Skip empty lines
        if not line:
            continue

        # Handle typedef declarations
        if line.startswith("typedef "):
            if line.endswith(";"):
                # Single-line typedef
                continue
            else:
                # Multi-line typedef (typedef struct/enum/etc.)
                typedef_brace_count = line.count('{') - line.count('}')
                in_typedef = True
                continue
        if in_typedef:
            # Update brace count
            typedef_brace_count += line.count('{') - line.count('}')
            if line.endswith(";"):
                # Only end typedef if we're at brace level 0 (outside of struct/enum body)
                if typedef_brace_count <= 0:
                    in_typedef = False
                    typedef_brace_count = 0
                # Continue regardless - we're still processing typedef content
                continue
            continue

        # Handle struct/class definitions (without implementation)
        # Handle single-line struct/class declarations
        if re.match(r"^(struct|class)\s+\w+(\s*:\s*[^{]+)?\s*{.*};\s*$", line):
            continue
        if re.match(r"^(struct|class)\s+\w+(\s*:\s*[^{]+)?\s*{", line):
            in_struct_or_class = True
            continue
        # Handle single-line enum declarations
        if re.match(r"^enum(\s+class)?\s+\w+(\s*:\s*\w+)?\s*{.*};\s*$", line):
            continue
        if re.match(r"^enum(\s+class)?\s+\w+(\s*:\s*\w+)?\s*{", line):
            in_enum = True
            continue
        if in_struct_or_class or in_enum:
            if "};" in line or line == "};":
                in_struct_or_class = False
                in_enum = False
            # Check for method implementations inside classes
            if re.match(r"^\s*\w+.*\(.*\)\s*{", line):
                return False
            continue

        # Handle namespace blocks
        if line.startswith("namespace ") and line.endswith("{"):
            in_namespace = True
            continue
        if in_namespace:
            if line == "}":
                in_namespace = False
                continue
            # Handle closing brace with optional content after it
            if line.endswith("}") and not line.endswith("};"):
                in_namespace = False
                continue
            # Continue processing namespace content with normal rules
            # Don't skip here, let it fall through to other checks
            pass

        # Skip extern declarations
        if line.startswith("extern "):
            continue
        # Skip forward declarations
        if line.startswith("class ") and line.endswith(";"):
            continue
        if line.startswith("struct ") and line.endswith(";"):
            continue
        # Skip using statements (C++)
        if line.startswith("using "):
            continue
        # Skip template declarations
        if line.startswith("template"):
            continue
        # Skip constants (C/C++ const are truly constant - compile-time immutable values)
        if line.startswith("const "):
            # Check if the constant is initialized with a function call
            # Simple check: look for "= identifier(" pattern
            if " = " in line and "(" in line and ")" in line:
                # More specific check to avoid false positives with string literals
                if re.search(r'=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
                    return False
            continue
        if line.startswith("static const "):
            # Check if the constant is initialized with a function call
            if " = " in line and "(" in line and ")" in line:
                if re.search(r'=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
                    return False
            continue
        if line.startswith("static "):
            # Check if the variable is initialized with a function call
            if " = " in line and "(" in line and ")" in line:
                if re.search(r'=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
                    return False
            continue
        if line.startswith("extern const "):
            continue
        # Skip enum declarations
        if line.startswith("enum ") and line.endswith(";"):
            continue
        # Skip macros (basic constants)
        if re.match(r"^#define\s+[A-Z_][A-Z0-9_]*\s+", line):
            continue
        # If we find any other code, it's not export-only
        return False

    return True

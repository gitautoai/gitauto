import re


def should_skip_javascript(content: str) -> bool:
    """
    Determines if a JavaScript/TypeScript file should be skipped for test generation.

    Returns True if the file contains only:
    - Import/export statements
    - Constants and literals
    - Type definitions (TypeScript interfaces, types, enums)
    - CommonJS require statements

    Returns False if the file contains:
    - Function definitions with logic
    - Arrow functions or function expressions
    - Class implementations with methods
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    code_lines = []

    # Remove comments and normalize whitespace
    in_multiline_comment = False
    in_interface_or_type = False
    in_enum = False

    for line in lines:
        line = line.strip()
        if "/*" in line:
            in_multiline_comment = True
        if in_multiline_comment:
            if "*/" in line:
                in_multiline_comment = False
            continue
        if line.startswith("//"):
            continue
        if line:
            code_lines.append(line)

    # Check if only export/import/constant/type statements
    for line in code_lines:
        # Skip import statements
        if line.startswith("import "):
            continue
        # Skip type imports (TypeScript)
        if line.startswith("import type ") or "import { type" in line:
            continue
        # Skip CommonJS require statements (const/let/var with require)
        if re.match(r"^(const|let|var)\s+\w+\s*=\s*require\(", line):
            continue
        # Skip destructured requires
        if re.match(r"^(const|let|var)\s+{.*}\s*=\s*require\(", line):
            continue
        # Skip export statements
        if line.startswith("export "):
            continue
        # Skip module.exports (including object literals)
        if line.startswith("module.exports") or line.startswith("exports."):
            continue
        # Skip standalone object literals that are simple exports
        if re.match(r"^\w+,?$", line):  # Simple property names in objects
            continue
        if line in ["{", "}", "};"]:  # Object literal braces
            continue
        # Skip export all statements
        if re.match(r"export\s*\*\s*from", line):
            continue
        # Skip export with braces
        if re.match(r"export\s*{.*}\s*from", line):
            continue
        # Skip default exports from other modules
        if re.match(r"export\s*{.*default.*}\s*from", line):
            continue

        # First check for function definitions - these should NOT be skipped
        if line.startswith("function ") or re.match(r"^\w+\s*\(.*\)\s*{", line):
            return False

        # Handle TypeScript type definitions
        if line.startswith("type ") and "=" in line:
            # Check if it's a multi-line type definition
            if "{" in line and "}" not in line:
                in_interface_or_type = True
            continue
        if line.startswith("interface "):
            if "{" in line:
                in_interface_or_type = True
            continue
        if line.startswith("enum "):
            if "{" in line:
                in_enum = True
            continue
        if in_interface_or_type or in_enum:
            if "}" in line:
                in_interface_or_type = False
                in_enum = False
            continue
        # Skip type annotations in interfaces/types (field: type format)
        if re.match(r"^\w+\??\s*:\s*", line):
            continue
        # Skip closing braces followed by semicolon (end of type definitions)
        if line in ("};", "}"):
            continue
        # Skip constant declarations (primitive values, objects, arrays, template literals)
        # Note: JS const is not truly constant (prevents reassignment, but objects can mutate)
        # However, files with only const declarations of literals are typically constants files
        # Exclude arrow functions and other function expressions
        if (
            re.match(
                r"^(const|let|var)\s+[A-Z_][A-Z0-9_]*\s*=\s*[\[\{\"'`\d\-\+]", line
            )
            and "=>" not in line
            and "function" not in line
        ):
            continue
        # Skip const with literal values, template literals, simple concatenations (but not functions)
        if (
            re.match(
                r"^const\s+\w+\s*=\s*(true|false|null|undefined|\d|[\"']|\`)", line
            )
            and "=>" not in line
            and "function" not in line
        ):
            continue
        # If we find any other code, it's not export-only
        return False

    # If we only found exports/imports/constants/types or file is empty, it's export-only
    return True

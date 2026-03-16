import re

from utils.logging.logging_config import logger


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
    # Skip files explicitly excluded from coverage via istanbul/c8 pragma
    if "/* istanbul ignore file */" in content or "/* c8 ignore file */" in content:
        logger.info("Skipping file: coverage ignore pragma found")
        return True

    lines = content.split("\n")
    code_lines: list[str] = []

    # Remove comments and normalize whitespace
    in_multiline_comment = False
    in_interface_or_type = False
    in_enum = False
    in_template_literal = False
    in_class_definition = False

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
        # Handle template literals (both `const x = \`...\`` and tagged templates like `gql\`...\``)
        if not in_template_literal and "`" in line:
            if (
                line.count("`") == 1
            ):  # Template literal starts (odd backtick = unclosed)
                in_template_literal = True
                if line:
                    code_lines.append(line)
                continue
        if in_template_literal:
            if line.endswith("`;") or "`;" in line:  # Template literal ends
                in_template_literal = False
            continue
        if line:
            code_lines.append(line)

    # Check if only export/import/constant/type statements
    for line in code_lines:
        # Skip import statements
        if line.startswith("import "):
            continue
        # Skip CommonJS require statements (const/let/var with require)
        if re.match(r"^(const|let|var)\s+\w+\s*=\s*require\(", line):
            continue
        # Skip destructured requires
        if re.match(r"^(const|let|var)\s+{.*}\s*=\s*require\(", line):
            continue
        # Skip export statements that are re-exports or simple declarations but NOT exported functions/classes/arrow functions with logic
        if line.startswith("export "):
            rest = line[len("export ") :]
            # export default, export { ... }, export * from, export type
            if rest.startswith(("default ", "{", "* ", "type ")):
                continue
            # export const/let/var with arrow function or function expression = real logic
            if "=>" in rest or "function" in rest:
                return False
            # export const/let/var with async = arrow function on next line
            if re.match(r"^(const|let|var)\s+\w+\s*=\s*async\s*\(", rest):
                return False
            # export function or export class with body = real logic
            if rest.startswith(("function ", "async function ")):
                return False
            # export interface (multi-line) - set flag to skip body lines
            if rest.startswith("interface "):
                in_interface_or_type = True
                continue
            # export enum (multi-line) - set flag to skip body lines
            if rest.startswith("enum "):
                in_enum = True
                continue
            if rest.startswith("class ") and "{}" not in rest:
                # Non-empty class - check if it has methods
                if re.match(r"^class\s+\w+(\s+extends\s+\w+)?\s*\{\s*\}$", rest):
                    continue
                if re.match(r"^class\s+\w+(\s+extends\s+\w+)?\s*\{$", rest):
                    in_class_definition = True
                    continue
                return False
            # Simple export (const X = value, etc.)
            continue
        # Skip module.exports (including object literals)
        if line.startswith("module.exports") or line.startswith("exports."):
            continue
        # Skip standalone object literals that are simple exports
        if re.match(r"^\w+,?$", line):  # Simple property names in objects
            continue
        # Skip tagged template literals (e.g. gql`...`, css`...`, html`...`)
        if re.match(r"^\w+`", line):
            continue

        # Handle class closing FIRST before general closing brace handling
        if in_class_definition and line == "}":
            in_class_definition = False
            continue
        if in_class_definition:
            # If there's anything inside the class, it's not empty
            return False

        if line in ["{", "}", "};"]:  # Object literal braces
            continue

        # First check for function definitions - these should NOT be skipped
        if line.startswith("function ") or re.match(r"^\w+\s*\(.*\)\s*{", line):
            return False

        # Skip empty class definitions (class Name {} or class Name extends Base {})
        # Handle single-line empty classes like: class Name {}
        if re.match(r"^class\s+\w+(\s+extends\s+\w+)?\s*\{\s*\}$", line):
            continue
        # Handle multi-line empty classes
        if re.match(r"^class\s+\w+(\s+extends\s+\w+)?\s*\{$", line):
            in_class_definition = True
            continue

        # Handle TypeScript type definitions
        if line.startswith("type ") and "=" in line:
            # Check if it's a multi-line type definition
            if "{" in line and "}" not in line:
                in_interface_or_type = True
            continue
        if line.startswith("interface "):
            in_interface_or_type = True
            continue
        if line.startswith("enum "):
            in_enum = True
            continue

        if in_interface_or_type or in_enum:
            # Simply continue processing lines inside interface/enum/type definitions
            continue
        # Skip type annotations in interfaces/types (field: type format)
        if re.match(r"^\w+\??\s*:\s*\w+", line):
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
            and not re.search(r"\w+\s*\(", line)  # Exclude function calls
        ):
            continue
        # Skip const with literal values, template literals, simple concatenations (but not functions)
        if (
            re.match(
                r"^const\s+\w+\s*=\s*(true|false|null|undefined|\d|[\"']|\`)", line
            )
            and "=>" not in line
            and "function" not in line
            and not re.search(r"\w+\s*\(", line)  # Exclude function calls
            and not re.search(r"\$\{", line)  # Exclude template literal expressions
        ):
            continue
        # If we find any other code, it's not export-only
        return False

    # If we only found exports/imports/constants/types or file is empty, it's export-only
    return True

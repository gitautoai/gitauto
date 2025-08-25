import re


def should_skip_ruby(content: str) -> bool:
    """
    Determines if a Ruby file should be skipped for test generation.

    Returns True if the file contains only:
    - Require statements
    - Constants (UPPERCASE)
    - Autoload declarations

    Returns False if the file contains:
    - Method definitions
    - Class implementations with methods
    - Any executable code beyond declarations
    """
    lines = content.split("\n")
    in_constant_definition = False
    brace_count = 0
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip comments
        if stripped_line.startswith("#"):
            continue
        # Skip empty lines
        if not stripped_line:
            continue
            
        # If we're inside a constant definition (multi-line hash/array)
        if in_constant_definition:
            # Count braces to track when we exit the definition
            brace_count += stripped_line.count("{") + stripped_line.count("[")
            brace_count -= stripped_line.count("}") + stripped_line.count("]")
            
            # If we've closed all braces, we're done with this constant
            if brace_count <= 0:
                in_constant_definition = False
                brace_count = 0
            continue
            
        # Skip require statements
        if stripped_line.startswith("require ") or stripped_line.startswith("require_relative "):
            continue
        # Skip autoload
        if stripped_line.startswith("autoload "):
            continue
            
        # Check for constants (Ruby constants are UPPERCASE)
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", stripped_line):
            # Check if this constant definition contains opening braces (multi-line)
            brace_count = stripped_line.count("{") + stripped_line.count("[")
            brace_count -= stripped_line.count("}") + stripped_line.count("]")
            
            if brace_count > 0:
                in_constant_definition = True
            continue
            
        # If we find any other code, it's not export-only
        return False

    return True
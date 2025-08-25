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
        
        # Skip empty lines
        if not stripped_line:
            continue
            
        # Remove inline comments for processing (but keep the line for other checks)
        code_part = stripped_line.split('#')[0].strip()
        
        # Skip lines that are only comments
        if not code_part:
            continue
            
        # If we're inside a constant definition (multi-line hash/array)
        if in_constant_definition:
            # Count braces to track when we exit the definition
            brace_count += code_part.count("{") + code_part.count("[")
            brace_count -= code_part.count("}") + code_part.count("]")
            
            # If we've closed all braces, we're done with this constant
            if brace_count <= 0:
                in_constant_definition = False
                brace_count = 0
            continue
            
        # Skip require statements
        if code_part.startswith("require ") or code_part.startswith("require_relative "):
            continue
        # Skip autoload
        if code_part.startswith("autoload "):
            continue
            
        # Check for constants (Ruby constants are UPPERCASE)
        if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", code_part):
            # Check if this constant definition contains opening braces (multi-line)
            brace_count = code_part.count("{") + code_part.count("[")
            brace_count -= code_part.count("}") + code_part.count("]")
            
            if brace_count > 0:
                in_constant_definition = True
            continue
            
        # If we find any other code, it's not export-only
        return False

    return True
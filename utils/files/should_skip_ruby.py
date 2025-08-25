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
            
        # Handle inline comments more carefully - only remove comments that are not in strings
        code_part = stripped_line
        # Simple approach: if line starts with #, it's a comment
        if stripped_line.startswith("#"):
            continue
            
        # For inline comments, we need to be more careful about strings
        # For now, let's use a simple heuristic: find # that's not inside quotes
        in_string = False
        quote_char = None
        comment_pos = -1
        
        for i, char in enumerate(stripped_line):
            if not in_string and char in ['"', "'"]:
                in_string = True
                quote_char = char
            elif in_string and char == quote_char and (i == 0 or stripped_line[i-1] != '\\'):
                in_string = False
                quote_char = None
            elif not in_string and char == '#':
                comment_pos = i
                break
                
        if comment_pos >= 0:
            code_part = stripped_line[:comment_pos].strip()
        
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
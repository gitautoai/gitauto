from utils.error.handle_exceptions import handle_exceptions

@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_code_files(filenames: list[str]):
    """Filter out test files and common non-code files"""
    # Common non-code file extensions
    non_code_extensions = [
        ".md",
        ".json",
        ".xml",
        ".yml",
        ".yaml",
        ".csv",
        ".html",
        ".css",
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".pdf",
        ".lock",
        ".env",
        ".txt"
    ]
    
    result = []
    
    for filename in filenames:
        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]
        
        # Filter out files with non-code extensions
        if any(lower_filename.endswith(ext) for ext in non_code_extensions):
            if not (lower_filename.endswith('.py') or lower_filename.endswith('.js') or lower_filename.endswith('.rb') or lower_filename.endswith('.go') or lower_filename.endswith('.sh')):
                continue
        
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            continue
        
        # Check for prefix/suffix patterns
        if any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            continue
        
        # Handle files with .py extension specially
        if basename.endswith(".py"):
            base_without_ext = basename[:-3]  # Remove .py extension
            if base_without_ext in ["mock", "stub", "fixture"] or basename.startswith("mock_") or basename.startswith("stub_") or basename.startswith("fixture_"):
                continue
            
            if basename in ["mockingbird.py", "stubborn.py", "fixtures.py"]:
                continue
        
        result.append(filename)
    
    return result

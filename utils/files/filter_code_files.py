from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_code_files(filenames: list[str]):
    """Filter out test files and common non-code files"""
    # File patterns that are likely tests or don't need tests
    test_patterns = [
        "test_",
        "_test.",
        "test.",
        "spec.",
        ".spec.",
        "tests/",
        "test/",
        "specs/",
        "__tests__/",
        "mock",
        "stub",
        "fixture",
    ]

    # Common non-code file extensions
    non_code_extensions = [
        ".md",
        ".txt",
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
    ]

    result = []
    for filename in filenames:
        # Skip obvious non-code files
        if any(filename.lower().endswith(ext) for ext in non_code_extensions):
            continue

        # Skip test files themselves
        lower_filename = filename.lower()
        
        # Special case for partial pattern matches
        # Words like "mockingbird", "stubborn", "fixtures" should not be filtered
        # unless they match specific patterns
        
        # Get just the filename without path
        filename_part = lower_filename.split('/')[-1]
        
        # Check for directory patterns first
        if any(pattern in lower_filename for pattern in ["tests/", "test/", "specs/", "__tests__/"]):
            continue
            
        # Check for test patterns
        if any(pattern in lower_filename for pattern in ["test_", "_test.", "test.", "spec.", ".spec."]):
            continue
            
        # Check for word-based patterns (mock, stub, fixture)
        # These should match as standalone words or with specific prefixes/suffixes
        should_skip = False
        for pattern in ["mock", "stub", "fixture"]:
            if pattern == filename_part or filename_part.startswith(f"{pattern}_") or \
               filename_part.startswith(f"{pattern}.") or f"_{pattern}" in filename_part or \
               f".{pattern}" in filename_part:
                should_skip = True
                break
                
        if should_skip:
            continue

        result.append(filename)

    return result
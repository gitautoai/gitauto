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

    # Files that should be filtered out based on exact name or pattern
    exact_filter_files = [
        "mock.py", 
        "stub.py", 
        "fixture.py",
        "fixtures.py",
        "mockingbird.py",
        "stubborn.py"
    ]
    
    # Patterns that should be filtered if they appear as prefixes or with underscores
    filter_patterns = [
        "mock_", "_mock", 
        "stub_", "_stub", 
        "fixture_", "_fixture"
    ]

    result = []
    for filename in filenames:
        # Skip obvious non-code files
        if any(filename.endswith(ext) for ext in non_code_extensions):
            continue

        # Skip test files themselves
        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]
        
        # Check for test patterns
        should_skip = False
        
        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
            
        # Check for prefix/suffix patterns
        elif any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            should_skip = True
            
        # Check for exact filenames to filter
        elif basename in exact_filter_files:
            should_skip = True
            
        # Check for patterns that should be filtered
        elif any(p in basename for p in filter_patterns):
            should_skip = True
        
        if should_skip:
            continue

        result.append(filename)

    return result
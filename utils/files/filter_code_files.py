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
    
    # Word patterns that should match exactly or at word boundaries
    word_patterns = [
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
        if any(filename.endswith(ext) for ext in non_code_extensions):
            continue

        # Skip test files themselves
        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]
        
        # Check for test patterns
        should_skip = False
        
        # Check for directory and prefix/suffix patterns
        if any(pattern in lower_filename for pattern in test_patterns):
            should_skip = True
            
        # Check for word patterns (mock, stub, fixture)
        for word in word_patterns:
            # Check if it's a standalone word or at word boundaries
            if basename == word + ".py" or basename.startswith(word + "_") or basename.endswith("s.py") and basename.startswith(word):
                should_skip = True
                break
        
        if should_skip:
            continue

        result.append(filename)

    return result
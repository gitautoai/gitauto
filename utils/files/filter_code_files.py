from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_code_files(filenames: list[str]):
    """Filter out test files and common non-code files"""
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
    # Word patterns that should be matched as whole words
    word_patterns = ["mock", "stub", "fixture"]

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
        basename = lower_filename.split('/')[-1]  # Get just the filename without path
        
        # Check for test patterns
        should_skip = False
        
        # Check for directory patterns
        if any(pattern in lower_filename for pattern in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
        
        # Check for prefix/suffix patterns
        elif any(pattern in basename for pattern in ["test_", "_test.", "test.", "spec.", ".spec."]):
            should_skip = True
        
        # Check for word patterns (mock, stub, fixture)
        # These should match as whole words, not as part of other words
        elif any(
            basename == pattern or 
            basename.startswith(f"{pattern}_") or
            basename.startswith(f"{pattern}.") or
            basename.endswith(f"_{pattern}") or
            f"_{pattern}_" in basename
            for pattern in word_patterns
        ):
            should_skip = True
        
        if should_skip:
            continue

        result.append(filename)

    return result

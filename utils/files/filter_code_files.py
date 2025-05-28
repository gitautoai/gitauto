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
        if any(filename.endswith(ext) for ext in non_code_extensions):
            continue

        # Skip test files themselves
        lower_filename = filename.lower()
        filename_part = lower_filename.split('/')[-1]  # Get just the filename without path
        
        # Check for test patterns
        should_skip = False
        
        # Check for directory patterns
        if any(pattern in lower_filename for pattern in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
        
        # Check for prefix patterns
        if any(filename_part.startswith(pattern) for pattern in ["test_", "test.", "spec."]):
            should_skip = True
        
        # Check for exact substring patterns
        if any(pattern in filename_part for pattern in ["_test.", ".spec."]):
            should_skip = True
        
        # Check for word-based patterns (mock, stub, fixture)
        # These should match as substrings but not within other words
        for pattern in ["mock", "stub", "fixture"]:
            if pattern in filename_part:
                # Check if it's at a word boundary
                pattern_start = filename_part.find(pattern)
                pattern_end = pattern_start + len(pattern)
                
                # Check if pattern is at the start of the filename
                if pattern_start == 0:
                    # Check what follows the pattern
                    if pattern_end == len(filename_part) or filename_part[pattern_end] in "._":
                        should_skip = True
                        break
                # Check if pattern is preceded by underscore or dot
                elif filename_part[pattern_start - 1] in "._":
                    should_skip = True
                    break
                # Special case: if pattern is the entire filename (no extension)
                elif filename_part == pattern:
                    should_skip = True
                    break
        
        if should_skip:
            continue

        result.append(filename)

    return result
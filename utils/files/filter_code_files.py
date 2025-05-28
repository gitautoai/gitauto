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
        basename = lower_filename.split('/')[-1]
        
        # Check for test patterns
        should_skip = False
        for pattern in test_patterns:
            # For directory patterns
            if pattern.endswith('/') and pattern in lower_filename:
                should_skip = True
                break
                
            # For prefix patterns
            elif pattern.startswith('test') or pattern.startswith('_test') or pattern.startswith('.spec'):
                if basename.startswith(pattern) or pattern in basename:
                    should_skip = True
                    break
                    
            # For exact word patterns (mock, stub, fixture)
            elif pattern in ["mock", "stub", "fixture"]:
                # Only match if it's a standalone word or at the beginning
                if basename == pattern + ".py" or basename.startswith(pattern + "_"):
                    should_skip = True
                    break
                    
            # For "spec." pattern
            elif pattern == "spec.":
                if basename == "spec.py" or ".spec." in basename:
                    should_skip = True
                    break
        
        if should_skip:
            continue

        result.append(filename)

    return result
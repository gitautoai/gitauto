from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_code_files(filenames: list[str]):
    """Filter out test files and common non-code files"""
    # Patterns for test identification
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

    # Word patterns for filtering files that look like test files
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

    # Special exceptions that should not be filtered out
    exceptions = [
        "contest.py",
        "respect.py",
        "testing.py",
    ]

    result = []
    for filename in filenames:
        # Skip obvious non-code files
        if any(filename.lower().endswith(ext) for ext in non_code_extensions):
            continue

        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]

        # If file is an exception, include it
        if basename in exceptions:
            result.append(filename)
            continue

        should_skip = False

        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
        # Check for prefix/suffix test patterns
        elif any(p in basename for p in test_patterns):
            should_skip = True
        else:
            # Check for word patterns at the beginning (based on filename without extension)
            name_without_ext = basename.rsplit('.', 1)[0]
            for p in word_patterns:
                if name_without_ext.startswith(p):
                    should_skip = True
                    break

        if not should_skip:
            result.append(filename)

    return result

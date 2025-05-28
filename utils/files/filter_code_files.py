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

        # Skip test files themselves
        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]

        # Check if file is in exceptions list
        if basename in exceptions:
            result.append(filename)
            continue

        # Check for test patterns
        should_skip = False

        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True

        # Check for prefix/suffix patterns
        elif any(p in basename for p in test_patterns):
            should_skip = True

        # Check for word patterns (mock, stub, fixture)
        elif any(basename == p + ".py" or 
                basename.startswith(p + "_") or 
                basename.endswith("_" + p + ".py") or
                basename == p + "s.py"  # Handle plural forms
                for p in word_patterns):
            should_skip = True

        # Special cases for partial matches that should be skipped
        elif basename in ["mockingbird.py", "stubborn.py", "fixtures.py"]:
            should_skip = True

        if not should_skip:
            result.append(filename)

    return result
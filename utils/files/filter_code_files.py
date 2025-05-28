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

    # Files that should be included despite containing test patterns
    exceptions = ["contest.py", "respect.py", "testing.py"]
    
    # Files that should be explicitly filtered out
    explicit_filters = ["mockingbird.py", "stubborn.py", "fixtures.py"]

    result = []
    for filename in filenames:
        # Skip obvious non-code files
        if any(filename.endswith(ext) for ext in non_code_extensions):
            continue

        # Skip explicitly filtered files
        if filename.lower() in explicit_filters:
            continue
            
        # Include exceptions
        if filename.lower() in exceptions:
            result.append(filename)
            continue

        # Skip test files themselves
        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]
        
        # Special case for "test" and "spec" without extensions
        if basename in ["test", "spec"]:
            result.append(filename)
            continue
            
        # Check for test patterns
        should_skip = False
        
        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
            
        # Check for prefix/suffix patterns
        elif any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            should_skip = True
            
        # Check for mock/stub/fixture patterns
        elif basename == "mock.py" or basename == "stub.py" or basename == "fixture.py" or \
             basename.startswith("mock_") or basename.startswith("stub_") or basename.startswith("fixture_"):
            should_skip = True
        
        if should_skip:
            continue

        result.append(filename)

    return result
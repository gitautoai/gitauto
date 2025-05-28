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
        
        should_skip = False
        for pattern in test_patterns:
            if pattern in ["tests/", "test/", "specs/", "__tests__/"]:
                # Directory patterns - check if path contains them
                if pattern in lower_filename:
                    should_skip = True
                    break
            elif pattern in ["test_", "test."]:
                # Prefix patterns - check if filename starts with them
                if filename_part.startswith(pattern):
                    should_skip = True
                    break
            elif pattern in ["_test.", ".spec."]:
                # Exact substring patterns - check if filename contains them
                if pattern in filename_part:
                    should_skip = True
                    break
            elif pattern == "spec.":
                # Prefix pattern for spec
                if filename_part.startswith(pattern):
                    should_skip = True
                    break
            elif pattern in ["mock", "stub", "fixture"]:
                # Word-based patterns - check if they appear as complete words or word parts
                if (pattern in filename_part and 
                    (filename_part.startswith(pattern) or 
                     "_" + pattern in filename_part or 
                     pattern + "_" in filename_part or
                     pattern + "." in filename_part)):
                    should_skip = True
                    break
        
        if should_skip:
            continue

        result.append(filename)

    return result
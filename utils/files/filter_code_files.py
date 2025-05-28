from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def filter_code_files(filenames: list[str]):
    """Filter out test files and common non-code files"""
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
        basename = lower_filename.split('/')[-1]
        
        # Check for test patterns
        should_skip = False
        
        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            should_skip = True
            
        # Check for prefix/suffix patterns
        elif any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            should_skip = True
            
        # Check for mock/stub/fixture patterns
        elif any(word in basename for word in ["mock", "stub", "fixture"]):
            # By default, skip files containing these patterns
            should_skip = True
            
            # Exception: If the file has no extension and is exactly 'mock', 'stub', or 'fixture', don't skip it
            if '.' not in basename and basename in {"mock", "stub", "fixture"}:
                should_skip = False
        
        if should_skip:
            continue

        result.append(filename)

    return result
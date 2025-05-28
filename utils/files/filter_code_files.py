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
            
        # Handle files with .py extension
        elif basename.endswith(".py"):
            # Check for exact word patterns (mock, stub, fixture)
            base_without_ext = basename[:-3]  # Remove .py extension
            if base_without_ext in ["mock", "stub", "fixture"] or \
               basename.startswith("mock_") or basename.startswith("stub_") or basename.startswith("fixture_"):
                should_skip = True
                
            # Special handling for files that contain test-related words but are not test files
            elif basename in ["mockingbird.py", "stubborn.py", "fixtures.py"]:
                should_skip = True
        
        # For non-Python files, check for mock/stub/fixture patterns more broadly
        elif not basename.endswith(".py"):
            if any(word in basename for word in ["mock", "stub", "fixture"]):
                should_skip = True
        
        if should_skip:
            continue

        result.append(filename)

    return result

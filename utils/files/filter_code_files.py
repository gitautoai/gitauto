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

        lower_filename = filename.lower()
        basename = lower_filename.split('/')[-1]
        
        # Exclude if path indicates test directories
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            continue
        
        # Exclude if filename contains common test prefixes/suffixes
        if any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            continue
        
        # Additional filtering for Python files
        if basename.endswith(".py"):
            base_without_ext = basename[:-3]  # Remove .py
            if base_without_ext in ["mock", "stub", "fixture"] or 
               base_without_ext.startswith("mock_") or base_without_ext.startswith("stub_") or base_without_ext.startswith("fixture_"):
                continue
            if basename in ["mockingbird.py", "stubborn.py", "fixtures.py"]:
                continue
        
        result.append(filename)
    return result

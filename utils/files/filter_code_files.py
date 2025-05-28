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
        
        # Check for directory patterns
        if any(p in lower_filename for p in ["tests/", "test/", "specs/", "__tests__/"]):
            continue
            
        # Check for prefix/suffix patterns
        if any(p in basename for p in ["test_", "_test.", "test.", "spec.", ".spec."]):
            continue
            
        # Handle files with .py extension
        if basename.endswith(".py") or basename.endswith(".PY") or basename.endswith(".Py") or basename.endswith(".pY"):
            # Check for exact word patterns (mock, stub, fixture)
            if basename in ["mock.py", "stub.py", "fixture.py"]:
                continue
                
            # Check for prefix patterns (mock_, stub_, fixture_)
            if basename.startswith("mock_") or basename.startswith("stub_") or basename.startswith("fixture_"):
                continue
                

        result.append(filename)

    return result

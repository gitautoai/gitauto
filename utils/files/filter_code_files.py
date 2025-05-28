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
            
        # Check for mock/stub/fixture patterns with word boundary logic
        elif not should_skip:
            for word in ["mock", "stub", "fixture"]:
                if word in basename:
                    # Check if it's a word boundary match
                    word_start = basename.find(word)
                    word_end = word_start + len(word)
                    
                    # Check if it's at the beginning or preceded by underscore/dot
                    starts_properly = word_start == 0 or basename[word_start - 1] in "._"
                    # Check if it's at the end or followed by underscore/dot
                    ends_properly = word_end == len(basename) or basename[word_end] in "._"
                    
                    if starts_properly and ends_properly:
                        should_skip = True
                        break
        
        if should_skip:
            continue

        result.append(filename)

    return result
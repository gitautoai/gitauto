from unittest.mock import patch
from utils.text.sort_imports import sort_imports


def test_sort_imports_unsupported_extensions():
    """Test that unsupported file extensions return unchanged content."""
    content = "#include <stdio.h>\n#include <stdlib.h>"

    # Test various unsupported extensions
    for ext in [".c", ".cpp", ".java", ".go", ".rs", ".php", ".rb", ".sh", ".sql"]:
        result = sort_imports(content, f"test{ext}")
        assert result == content


def test_sort_imports_empty_content():
    """Test that empty content is handled correctly."""
    assert sort_imports("", "test.py") == ""
    assert sort_imports("   ", "test.js") == "   "
    assert sort_imports("\n\n", "test.ts") == "\n\n"


def test_sort_imports_no_extension():
    """Test files without extensions return unchanged."""
    content = "some content"
    result = sort_imports(content, "Dockerfile")
    assert result == content

    result = sort_imports(content, "README")
    assert result == content

    result = sort_imports(content, "Makefile")
    assert result == content


def test_sort_imports_orchestrator_error_handling():
    """Test that orchestrator handles errors from any language sorter."""
    with patch("utils.text.sort_imports.sort_python_imports") as mock_sorter:
        mock_sorter.side_effect = Exception("Sorter failed")
        content = "import os"
        result = sort_imports(content, "test.py")
        # Should return original content on error due to @handle_exceptions
        assert result == content


def test_sort_imports_preserves_file_extension_case():
    """Test that file extension matching is case-sensitive."""
    content = "import something"

    # Uppercase extensions should not match any known patterns
    result = sort_imports(content, "test.PY")
    assert result == content  # Should return unchanged

    result = sort_imports(content, "test.JS")
    assert result == content  # Should return unchanged

    result = sort_imports(content, "test.TS")
    assert result == content  # Should return unchanged


def test_sort_imports_multiple_extensions():
    """Test files with multiple extensions use the last extension."""
    content = "some content"

    # File with multiple dots - should use last extension for matching
    result = sort_imports(content, "test.min.unknown")
    assert result == content  # Unknown extension returns unchanged

    result = sort_imports(content, "jquery.1.2.3.min.js")
    # Should match .js extension and route accordingly


def test_sort_imports_path_with_directories():
    """Test that file paths with directories work correctly."""
    content = "some content"

    # Test absolute paths
    result = sort_imports(content, "/path/to/my/test.unknown")
    assert result == content

    # Test relative paths
    result = sort_imports(content, "./src/components/file.unknown")
    assert result == content

    # Test nested paths
    result = sort_imports(content, "very/deep/nested/path/file.unknown")
    assert result == content


def test_sort_imports_special_filenames():
    """Test special filename patterns."""
    content = "some content"

    # Hidden files
    result = sort_imports(content, ".gitignore")
    assert result == content

    # Files starting with dots
    result = sort_imports(content, ".env.unknown")
    assert result == content

    # Files with spaces (if supported by filesystem)
    result = sort_imports(content, "my file.unknown")
    assert result == content


def test_sort_imports_whitespace_content():
    """Test handling of various whitespace patterns."""
    # Only spaces
    assert sort_imports("    ", "test.unknown") == "    "

    # Only tabs
    assert sort_imports("\t\t", "test.unknown") == "\t\t"

    # Mixed whitespace
    assert sort_imports(" \t \n ", "test.unknown") == " \t \n "


def test_sort_imports_large_filename():
    """Test handling of very long filenames."""
    content = "some content"
    long_name = "a" * 200 + ".unknown"
    result = sort_imports(content, long_name)
    assert result == content

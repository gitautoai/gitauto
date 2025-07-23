import os
import pytest
from unittest.mock import mock_open, patch, MagicMock
from utils.files.get_file_content import get_file_content


def test_get_file_content_success():
    """Test that get_file_content correctly reads file content."""
    file_content = "Hello, World!\nThis is a test file."
    
    with patch("builtins.open", mock_open(read_data=file_content)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("test.txt")
    
    assert result == file_content


def test_get_file_content_empty_file():
    """Test that get_file_content correctly handles empty files."""
    with patch("builtins.open", mock_open(read_data="")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("empty.txt")
    
    assert result == ""


def test_get_file_content_file_with_newlines():
    """Test that get_file_content preserves newlines in file content."""
    file_content = "Line 1\nLine 2\n\nLine 4\n"
    
    with patch("builtins.open", mock_open(read_data=file_content)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("multiline.txt")
    
    assert result == file_content


def test_get_file_content_file_with_unicode():
    """Test that get_file_content correctly handles Unicode characters."""
    file_content = "Hello 世界! 🌍 Café naïve résumé"
    
    with patch("builtins.open", mock_open(read_data=file_content)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("unicode.txt")
    
    assert result == file_content


def test_get_file_content_large_file():
    """Test that get_file_content handles large file content."""
    file_content = "A" * 10000 + "\n" + "B" * 10000
    
    with patch("builtins.open", mock_open(read_data=file_content)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("large.txt")
    
    assert result == file_content


def test_get_file_content_file_not_found():
    """Test that get_file_content returns empty string when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
        with patch("os.path.exists", return_value=False):
            result = get_file_content("nonexistent.txt")
    
    assert result == ""


def test_get_file_content_permission_error():
    """Test that get_file_content returns empty string on permission error."""
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("protected.txt")
    
    assert result == ""


def test_get_file_content_is_directory_error():
    """Test that get_file_content returns empty string when path is a directory."""
    with patch("builtins.open", side_effect=IsADirectoryError("Is a directory")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("directory/")
    
    assert result == ""


def test_get_file_content_encoding_error():
    """Test that get_file_content returns empty string on encoding error."""
    with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("binary.bin")
    
    assert result == ""


def test_get_file_content_io_error():
    """Test that get_file_content returns empty string on IO error."""
    with patch("builtins.open", side_effect=IOError("IO error occurred")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("corrupted.txt")
    
    assert result == ""


def test_get_file_content_uses_correct_encoding():
    """Test that get_file_content uses UTF-8 encoding."""
    with patch("builtins.open", mock_open(read_data="test")) as mock_file:
        with patch("os.path.exists", return_value=True):
            get_file_content("test.txt")
    
    # Verify that open was called with correct parameters
    mock_file.assert_called_once_with(file="test.txt", mode="r", encoding="utf-8", newline="\n")


def test_get_file_content_uses_correct_newline():
    """Test that get_file_content uses correct newline parameter."""
    with patch("builtins.open", mock_open(read_data="line1\nline2")) as mock_file:
        with patch("os.path.exists", return_value=True):
            get_file_content("test.txt")
    
    # Verify that open was called with newline="\n"
    mock_file.assert_called_once_with(file="test.txt", mode="r", encoding="utf-8", newline="\n")


def test_get_file_content_prints_file_exists_debug():
    """Test that get_file_content prints debug information about file existence."""
    with patch("builtins.open", mock_open(read_data="test")):
        with patch("os.path.exists", return_value=True) as mock_exists:
            with patch("builtins.print") as mock_print:
                get_file_content("test.txt")
    
    # Verify that os.path.exists was called
    mock_exists.assert_called_once_with("test.txt")
    
    # Verify that print was called with the correct message
    mock_print.assert_called_once_with("get_file_content - file exists: True")


def test_get_file_content_prints_file_not_exists_debug():
    """Test that get_file_content prints debug information when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with patch("os.path.exists", return_value=False) as mock_exists:
            with patch("builtins.print") as mock_print:
                get_file_content("nonexistent.txt")
    
    # Verify that os.path.exists was called
    mock_exists.assert_called_once_with("nonexistent.txt")
    
    # Verify that print was called with the correct message
    mock_print.assert_called_once_with("get_file_content - file exists: False")


def test_get_file_content_with_different_file_paths():
    """Test that get_file_content works with various file path formats."""
    test_cases = [
        "simple.txt",
        "path/to/file.txt",
        "/absolute/path/file.txt",
        "../relative/path/file.txt",
        "./current/dir/file.txt",
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.with.dots.txt",
        "UPPERCASE.TXT"
    ]
    
    for file_path in test_cases:
        with patch("builtins.open", mock_open(read_data="content")):
            with patch("os.path.exists", return_value=True):
                result = get_file_content(file_path)
        
        assert result == "content", f"Failed for file path: {file_path}"


def test_get_file_content_with_special_characters():
    """Test that get_file_content handles file content with special characters."""
    special_content = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?\n\t\r"
    
    with patch("builtins.open", mock_open(read_data=special_content)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("special.txt")
    
    assert result == special_content


def test_get_file_content_preserves_whitespace():
    """Test that get_file_content preserves leading and trailing whitespace."""
    content_with_whitespace = "  \n  Content with spaces  \n  "
    
    with patch("builtins.open", mock_open(read_data=content_with_whitespace)):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("whitespace.txt")
    
    assert result == content_with_whitespace


def test_get_file_content_exception_handling_behavior():
    """Test that get_file_content uses handle_exceptions decorator correctly."""
    # Test that exceptions are caught and default return value is returned
    with patch("builtins.open", side_effect=Exception("Unexpected error")):
        with patch("os.path.exists", return_value=True):
            result = get_file_content("error.txt")
    
    # Should return empty string (default_return_value) instead of raising
    assert result == ""

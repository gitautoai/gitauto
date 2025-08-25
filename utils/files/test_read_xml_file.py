from unittest.mock import mock_open, patch

import pytest
from utils.files.read_xml_file import read_xml_file


def test_read_xml_file_success():
    """Test that read_xml_file correctly reads and strips content from a file."""
    xml_content = "<root>\n  <element>Test</element>\n</root>\n"
    expected_content = "<root>\n  <element>Test</element>\n</root>"

    with patch("builtins.open", mock_open(read_data=xml_content)):
        result = read_xml_file("test.xml")

    assert result == expected_content


def test_read_xml_file_empty():
    """Test that read_xml_file correctly handles empty files."""
    with patch("builtins.open", mock_open(read_data="")):
        result = read_xml_file("empty.xml")

    assert result == ""


def test_read_xml_file_whitespace_only():
    """Test that read_xml_file correctly strips whitespace-only files."""
    with patch("builtins.open", mock_open(read_data="  \n  \t  \n  ")):
        result = read_xml_file("whitespace.xml")

    assert result == ""


def test_read_xml_file_with_leading_trailing_whitespace():
    """Test that read_xml_file correctly strips leading and trailing whitespace."""
    xml_content = "\n\n<root>\n  <element>Test</element>\n</root>\n\n"
    expected_content = "<root>\n  <element>Test</element>\n</root>"

    with patch("builtins.open", mock_open(read_data=xml_content)):
        result = read_xml_file("test.xml")

    assert result == expected_content


def test_read_xml_file_file_not_found():
    """Test that read_xml_file raises FileNotFoundError when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            read_xml_file("nonexistent.xml")


def test_read_xml_file_permission_error():
    """Test that read_xml_file raises PermissionError when file can't be accessed."""
    with patch("builtins.open", side_effect=PermissionError()):
        with pytest.raises(PermissionError):
            read_xml_file("protected.xml")


def test_read_xml_file_is_directory_error():
    """Test that read_xml_file raises IsADirectoryError when path is a directory."""
    with patch("builtins.open", side_effect=IsADirectoryError()):
        with pytest.raises(IsADirectoryError):
            read_xml_file("directory/")


def test_read_xml_file_encoding():
    """Test that read_xml_file uses utf-8 encoding."""
    with patch("builtins.open", mock_open(read_data="<root>Test</root>")) as mock_file:
        read_xml_file("test.xml")

    # Verify that open was called with the correct encoding
    mock_file.assert_called_once_with("test.xml", "r", encoding="utf-8")

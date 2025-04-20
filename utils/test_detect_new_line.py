import pytest
from utils.detect_new_line import detect_line_break


def test_detect_line_break_crlf():
    """Test detection of CRLF line breaks (Windows)."""
    text = "Hello\r\nWorld"
    assert detect_line_break(text) == "\r\n"


def test_detect_line_break_cr():
    """Test detection of CR line breaks (old Mac)."""
    text = "Hello\rWorld"
    assert detect_line_break(text) == "\r"


def test_detect_line_break_lf():
    """Test detection of LF line breaks (Unix/Linux/macOS)."""
    text = "Hello\nWorld"
    assert detect_line_break(text) == "\n"


def test_detect_line_break_empty_string():
    """Test detection of line breaks in an empty string."""
    text = ""
    assert detect_line_break(text) == "\n"


def test_detect_line_break_no_line_breaks():
    """Test detection when there are no line breaks in the text."""
    text = "HelloWorld"
    assert detect_line_break(text) == "\n"


def test_detect_line_break_mixed_line_breaks():
    """Test detection when there are mixed line breaks in the text."""
    text = "Hello\r\nWorld\rFoo\nBar"
    assert detect_line_break(text) == "\r\n"


def test_detect_line_break_crlf_at_end():
    """Test detection when CRLF is at the end of the text."""
    text = "HelloWorld\r\n"
    assert detect_line_break(text) == "\r\n"


def test_detect_line_break_cr_at_end():
    """Test detection when CR is at the end of the text."""
    text = "HelloWorld\r"
    assert detect_line_break(text) == "\r"
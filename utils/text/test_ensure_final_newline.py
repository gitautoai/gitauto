from utils.text.ensure_final_newline import ensure_final_newline


def test_ensure_final_newline_missing():
    text = "line1\nline2\nline3"
    expected = "line1\nline2\nline3\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_already_present():
    text = "line1\nline2\nline3\n"
    expected = "line1\nline2\nline3\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_crlf():
    text = "line1\r\nline2\r\nline3"
    expected = "line1\r\nline2\r\nline3\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_already_crlf():
    text = "line1\r\nline2\r\nline3\r\n"
    expected = "line1\r\nline2\r\nline3\r\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_empty():
    text = ""
    expected = ""
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_single_line():
    text = "single line"
    expected = "single line\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_whitespace_only():
    text = "   \t  "
    expected = "   \t  \n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_only_newline():
    text = "\n"
    expected = "\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_only_crlf():
    text = "\r\n"
    expected = "\r\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_mixed_line_endings():
    text = "line1\nline2\r\nline3"
    expected = "line1\nline2\r\nline3\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_multiple_trailing_newlines():
    text = "line1\nline2\n\n"
    expected = "line1\nline2\n\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_carriage_return_only():
    # Test with just \r (not \r\n) - should add \n
    text = "line1\rline2"
    expected = "line1\rline2\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_ends_with_carriage_return():
    # Test text ending with \r only (not \r\n) - should add \n
    text = "line1\nline2\r"
    expected = "line1\nline2\r\n"
    assert ensure_final_newline(text) == expected


def test_ensure_final_newline_unicode_content():
    text = "Hello 世界! 🌍"

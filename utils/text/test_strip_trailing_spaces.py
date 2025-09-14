from utils.text.strip_trailing_spaces import strip_trailing_spaces


def test_strip_trailing_spaces_basic():
    text = "line1   \nline2\t\nline3"
    expected = "line1\nline2\nline3"
    assert strip_trailing_spaces(text) == expected


def test_strip_trailing_spaces_mixed_endings():
    text = "line1   \nline2\t\r\nline3  "
    expected = "line1\nline2\r\nline3"
    assert strip_trailing_spaces(text) == expected


def test_strip_trailing_spaces_empty_lines():
    text = "line1\n   \nline3"
    expected = "line1\n\nline3"
    assert strip_trailing_spaces(text) == expected


def test_strip_trailing_spaces_no_trailing():
    text = "line1\nline2\nline3"
    expected = "line1\nline2\nline3"
    assert strip_trailing_spaces(text) == expected


def test_strip_trailing_spaces_empty():
    text = ""
    expected = ""
    assert strip_trailing_spaces(text) == expected

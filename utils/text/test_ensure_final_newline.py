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

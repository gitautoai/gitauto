from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes


def test_simple_color_codes():
    input_text = "\x1b[31mred\x1b[0m"
    expected = "red"
    result = remove_ansi_escape_codes(input_text)
    assert result == expected


def test_cursor_movement():
    input_text = "\x1b[2Kcleared line"
    expected = "cleared line"
    result = remove_ansi_escape_codes(input_text)
    assert result == expected


def test_multiple_codes():
    input_text = "\x1b[1m\x1b[31mbold red\x1b[0m normal"
    expected = "bold red normal"
    result = remove_ansi_escape_codes(input_text)
    assert result == expected

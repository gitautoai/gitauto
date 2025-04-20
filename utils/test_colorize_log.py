import pytest
from utils.colorize_log import colorize, ANSI_COLORS, ANSI_RESET, ColorType


def test_colorize_all_colors():
    test_text = "test"
    for color in ANSI_COLORS:
        result = colorize(test_text, color)
        expected = f"{ANSI_COLORS[color]}{test_text}{ANSI_RESET}"
        assert result == expected


def test_colorize_empty_string():
    for color in ANSI_COLORS:
        result = colorize("", color)
        expected = f"{ANSI_COLORS[color]}{ANSI_RESET}"
        assert result == expected


def test_colorize_invalid_color():
    with pytest.raises(KeyError):
        colorize("test", "invalid_color")


def test_colorize_specific_colors():
    # Test each color individually to ensure complete coverage
    assert colorize("error", "red") == f"{ANSI_COLORS['red']}error{ANSI_RESET}"
    assert colorize("success", "green") == f"{ANSI_COLORS['green']}success{ANSI_RESET}"
    assert colorize("warning", "yellow") == f"{ANSI_COLORS['yellow']}warning{ANSI_RESET}"
    assert colorize("info", "blue") == f"{ANSI_COLORS['blue']}info{ANSI_RESET}"
    assert colorize("debug", "magenta") == f"{ANSI_COLORS['magenta']}debug{ANSI_RESET}"
    assert colorize("notice", "cyan") == f"{ANSI_COLORS['cyan']}notice{ANSI_RESET}"


def test_colorize_multiline_text():
    multiline_text = "line1\nline2\nline3"
    for color in ANSI_COLORS:
        result = colorize(multiline_text, color)
        expected = f"{ANSI_COLORS[color]}{multiline_text}{ANSI_RESET}"
        assert result == expected


def test_colorize_special_characters():
    special_text = "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
    for color in ANSI_COLORS:
        result = colorize(special_text, color)
        expected = f"{ANSI_COLORS[color]}{special_text}{ANSI_RESET}"
        assert result == expected
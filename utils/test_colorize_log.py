import pytest
from utils.colorize_log import colorize, ANSI_COLORS, ANSI_RESET


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


def test_colorize_special_characters():
    special_text = "!@#$%^&*()"
    for color in ANSI_COLORS:
        result = colorize(special_text, color)
        expected = f"{ANSI_COLORS[color]}{special_text}{ANSI_RESET}"
        assert result == expected


def test_colorize_multiline_text():
    multiline_text = "line1\nline2\nline3"
    for color in ANSI_COLORS:
        result = colorize(multiline_text, color)
        expected = f"{ANSI_COLORS[color]}{multiline_text}{ANSI_RESET}"
        assert result == expected


def test_colorize_unicode_text():
    unicode_text = "こんにちは世界"  # Hello World in Japanese
    for color in ANSI_COLORS:
        result = colorize(unicode_text, color)
        expected = f"{ANSI_COLORS[color]}{unicode_text}{ANSI_RESET}"
        assert result == expected
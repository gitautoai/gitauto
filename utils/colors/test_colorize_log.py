import pytest
from utils.colors.colorize_log import colorize, ANSI_COLORS, ANSI_RESET


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

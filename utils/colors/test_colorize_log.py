from utils.colors.colorize_log import colorize, ANSI_COLORS, ANSI_RESET


def test_colorize_all_colors():
    test_text = "test"
    for color, color_code in ANSI_COLORS.items():
        result = colorize(test_text, color)
        expected = f"{color_code}{test_text}{ANSI_RESET}"
        assert result == expected


def test_colorize_empty_string():
    for color, color_code in ANSI_COLORS.items():
        result = colorize("", color)
        expected = f"{color_code}{ANSI_RESET}"
        assert result == expected

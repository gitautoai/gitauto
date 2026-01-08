from typing import Literal

ColorType = Literal["red", "green", "yellow", "blue", "magenta", "cyan"]

ANSI_COLORS: dict[ColorType, str] = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}
ANSI_RESET = "\033[0m"


def colorize(text: str, color: ColorType) -> str:
    return f"{ANSI_COLORS[color]}{text}{ANSI_RESET}"

from typing import Optional

WIDTH = 50
TOTAL = 100
messages: dict[int, str] = {
    0: "Let's get started!",
    10: "Making a start!",
    20: "Progressing...",
    30: "On the way...",
    40: "Almost halfway!",
    50: "Halfway there!",
    60: "More than halfway!",
    70: "Getting closer!",
    80: "Nearly there!",
    90: "Almost done!",
    100: "Completed!",
}


def generate_progress_bar(p: int, msg: Optional[str] = None) -> str:
    """
    Generates a markdown string for a progress bar.

    :param p: The progress percentage (0-100).
    :return: A markdown string for the progress bar.
    """
    if msg:
        message = msg
    elif p not in messages:
        message = messages[20]
    else:
        message = messages[p]

    ratio = p / TOTAL
    filled_length = int(WIDTH * ratio)
    unfilled_length = WIDTH - filled_length
    progress_bar = "▓" * filled_length + "░" * unfilled_length
    return f"{progress_bar} {int(ratio * 100)}%\n{message}"

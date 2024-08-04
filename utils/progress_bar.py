from typing import Optional

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


def generate_progress_bar(
    p: int, w=800, title="progress", msg: Optional[str] = None
) -> str:
    """
    Generates a markdown string for a progress bar. https://github.com/fredericojordan/progress-bar

    :param p: The progress percentage (0-100).
    :param w: The width of the progress bar in pixels.
    :return: A markdown string for the progress bar.
    """
    if msg:
        message = msg
    elif p not in messages:
        message = messages[20]
    else:
        message = messages[p]

    return f"![{message}](https://progress-bar.dev/{p}/?title={title}&width={w})\n{message}"

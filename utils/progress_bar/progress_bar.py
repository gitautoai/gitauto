WIDTH = 50


def create_progress_bar(p: int, msg: str) -> str:
    p = min(p, 95)
    ratio = p / 100
    filled_length = int(WIDTH * ratio)
    unfilled_length = WIDTH - filled_length
    progress_bar = "▓" * filled_length + "░" * unfilled_length
    return f"{progress_bar} {p}%\n{msg}"

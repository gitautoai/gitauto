def detect_line_break(text: str) -> str:
    """Detect the first line break in the text. It ignores the rest of the line breaks."""

    # CRLF (Windows)
    if "\r\n" in text:
        return "\r\n"

    # CR (old Mac)
    if "\r" in text:
        return "\r"

    # LF (Unix, Linux, macOS)
    return "\n"

def ensure_final_newline(text: str):
    if not text:
        return text

    # Ensure file ends with a newline if it has content
    if not text.endswith(("\n", "\r\n")):
        text += "\n"

    return text

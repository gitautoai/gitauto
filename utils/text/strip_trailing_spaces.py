def strip_trailing_spaces(text: str):
    lines = text.splitlines(keepends=True)
    stripped_lines = []

    for line in lines:
        if line.endswith("\r\n"):
            stripped_line = line.rstrip(" \t\r\n") + "\r\n"
        elif line.endswith("\n"):
            stripped_line = line.rstrip(" \t\n") + "\n"
        else:
            stripped_line = line.rstrip(" \t")
        stripped_lines.append(stripped_line)

    return "".join(stripped_lines)

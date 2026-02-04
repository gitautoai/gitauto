from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def format_content_with_line_numbers(*, file_path: str, content: str):
    """Format file content with line numbers in a code fence block."""
    lines = content.split("\n")
    width = len(str(len(lines)))
    numbered_lines = [f"{i + 1:>{width}}:{line}" for i, line in enumerate(lines)]
    numbered_content = "\n".join(numbered_lines)
    return f"```{file_path}\n{numbered_content}\n```"

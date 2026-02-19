import base64
import os

from anthropic.types import ToolUnionParam

from config import UTF8
from services.claude.tools.properties import (
    END_LINE,
    FILE_PATH,
    KEYWORD,
    LINE_NUMBER,
    START_LINE,
)
from services.github.types.github_types import BaseArgs
from services.openai.vision import describe_image
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.new_lines.detect_new_line import detect_line_break

# NOTE: No strict=True here because line_number, keyword, start_line, end_line are optional
GET_LOCAL_FILE_CONTENT: ToolUnionParam = {
    "name": "get_local_file_content",
    "description": "Reads the content of a file from the local clone. Can read any file on disk including those not tracked by git (e.g., node_modules). IMPORTANT: Always read the FULL file by default - do NOT use start_line/end_line/line_number/keyword to truncate the read. Only use start_line/end_line for files over 2000 lines. Truncating reads causes you to miss critical context like required fields, data structures, and execution order.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
            "line_number": LINE_NUMBER,
            "keyword": KEYWORD,
            "start_line": START_LINE,
            "end_line": END_LINE,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
}

# Full file read only (for PR handlers that need full context)
GET_LOCAL_FILE_CONTENT_FULL_ONLY: ToolUnionParam = {
    **GET_LOCAL_FILE_CONTENT,
    "input_schema": {
        "type": "object",
        "properties": {"file_path": FILE_PATH},
        "required": ["file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_local_file_content(
    file_path: str,
    base_args: BaseArgs,
    line_number: int | None = None,
    keyword: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    **_kwargs,
):
    # Validate parameter combinations
    has_line_number = line_number is not None
    has_keyword = keyword is not None
    has_range = start_line is not None or end_line is not None

    param_count = sum([has_line_number, has_keyword, has_range])
    if param_count > 1:
        return "Error: You can only specify one of: line_number, keyword, or start_line/end_line range."

    # Convert parameters to int if they're strings
    if line_number is not None and isinstance(line_number, str):
        try:
            line_number = int(line_number)
        except ValueError:
            return f"Error: line_number '{line_number}' is not a valid integer."

    if start_line is not None and isinstance(start_line, str):
        try:
            start_line = int(start_line)
        except ValueError:
            return f"Error: start_line '{start_line}' is not a valid integer."

    if end_line is not None and isinstance(end_line, str):
        try:
            end_line = int(end_line)
        except ValueError:
            return f"Error: end_line '{end_line}' is not a valid integer."

    # Validate start_line <= end_line
    if start_line is not None and end_line is not None and start_line > end_line:
        return "Error: start_line must be less than or equal to end_line."

    clone_dir = base_args["clone_dir"]
    full_path = os.path.join(clone_dir, file_path.strip("/"))

    if not os.path.exists(full_path):
        return f"File not found: '{file_path}'. Check the file path and try again."

    if not os.path.isfile(full_path):
        return f"'{file_path}' is a directory, not a file. Use get_local_file_tree to list directory contents."

    # Handle image files
    if file_path.endswith((".png", ".jpeg", ".jpg", ".webp", ".gif")):
        with open(full_path, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode(UTF8)
        msg = f"Opened image file: '{file_path}' and described the content.\n\n"
        return msg + describe_image(base64_image=encoded_content)

    # Read text file
    try:
        with open(full_path, "r", encoding=UTF8) as f:
            content = f.read()
    except UnicodeDecodeError:
        return f"Error: '{file_path}' is a binary file and cannot be read as text."

    lb = detect_line_break(text=content)
    lines = content.split(lb)

    # Ignore truncation parameters for files under 2000 lines to prevent missing context
    if len(lines) < 2000:
        line_number = None
        keyword = None
        start_line = None
        end_line = None

    width = len(str(len(lines)))
    numbered_lines = [f"{i + 1:>{width}}:{line}" for i, line in enumerate(lines)]
    file_path_with_lines = file_path

    # If start_line or end_line are specified, show the specified range
    if start_line is not None or end_line is not None:
        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = len(lines)

        start_idx = max(start_line - 1, 0)
        end_idx = min(end_line - 1, len(lines) - 1)
        numbered_lines = numbered_lines[start_idx : end_idx + 1]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start_line}-L{end_line}"

    # If line_number is specified, show the lines around the line_number
    elif line_number is not None and line_number > 1 and len(lines) > 100:
        buffer = 50
        start = max(line_number - buffer, 0)
        end = min(line_number + buffer, len(lines))
        numbered_lines = numbered_lines[start : end + 1]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start + 1}-L{end + 1}"

    # If keyword is specified, show the lines containing the keyword
    elif keyword is not None:
        buffer = 50
        segments: list[str] = []
        for i, line in enumerate(lines):
            if keyword not in line:
                continue
            start = max(i - buffer, 0)
            end = min(i + buffer, len(lines))
            segment = lb.join(numbered_lines[start : end + 1])  # noqa: E203
            file_path_with_lines = f"{file_path}#L{start + 1}-L{end + 1}"
            segments.append(f"```{file_path_with_lines}\n" + segment + "\n```")

        if not segments:
            return f"Keyword '{keyword}' not found in the file '{file_path}'."
        return "\n\n...\n\n".join(segments)

    numbered_content = lb.join(numbered_lines)
    if not numbered_content:
        logger.info("File '%s' is empty.", file_path)
    return f"```{file_path_with_lines}\n{numbered_content}\n```"

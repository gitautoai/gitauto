# Standard imports
import base64
import json
from typing import Optional

# Third-party imports
import requests

# Local imports
from config import (
    GITHUB_API_URL,
    TIMEOUT,
    UTF8,
)

# Local imports (GitHub)
from services.github.utils.create_headers import create_headers
from services.github.types.github_types import BaseArgs

# Local imports (OpenAI & Supabase)
from services.openai.vision import describe_image

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.new_lines.detect_new_line import detect_line_break


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_remote_file_content(
    file_path: str,
    base_args: BaseArgs,
    line_number: Optional[int] = None,
    keyword: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    **_kwargs,
):
    """
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28

    params:
    - file_path: file path or directory path. Ex) 'src/main.py' or 'src'
    - line_number: specific line number to focus on
    - keyword: keyword to search in the file content
    - start_line: starting line number for range
    - end_line: ending line number for range
    """
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

    owner, repo, ref, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["new_branch"],
        base_args["token"],
    )
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # If 404 error, return early. Otherwise, raise a HTTPError
    if response.status_code == 404:
        return f"{get_remote_file_content.__name__} encountered an HTTPError: 404 Client Error: Not Found for url: {url}. Check the file path, correct it, and try again."
    response.raise_for_status()

    # file_path is expected to be a file path, but it can be a directory path due to AI's volatility. See Example2 at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
    res_json = response.json()
    if not isinstance(res_json, dict):
        file_paths: list[str] = [item["path"] for item in res_json]
        msg = f"Searched directory '{file_path}' and found: {json.dumps(file_paths)}"
        return msg

    encoded_content: str = res_json["content"]  # Base64 encoded content

    # If encoded_content is image, describe the image content in text by vision API
    if file_path.endswith((".png", ".jpeg", ".jpg", ".webp", ".gif")):
        msg = f"Opened image file: '{file_path}' and described the content.\n\n"
        return msg + describe_image(base64_image=encoded_content)

    # Otherwise, decode the content
    decoded_content: str = base64.b64decode(s=encoded_content).decode(encoding=UTF8)
    lb: str = detect_line_break(text=decoded_content)
    lines = decoded_content.split(lb)
    width = len(str(len(lines)))
    numbered_lines = [f"{i + 1:>{width}}:{line}" for i, line in enumerate(lines)]
    file_path_with_lines = file_path

    # If start_line or end_line are specified, show the specified range
    if start_line is not None or end_line is not None:
        # Apply defaults
        if start_line is None:
            start_line = 1  # Default to beginning of file
        if end_line is None:
            end_line = len(lines)  # Default to end of file

        # Convert to 0-based indexing
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
        segments = []
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
        msg = f"Opened file: '{file_path}' and found multiple occurrences of '{keyword}'.\n\n"
        return msg + "\n\n•\n•\n•\n\n".join(segments)

    numbered_content: str = lb.join(numbered_lines)
    msg = f"Opened file: '{file_path}' with line numbers for your information.\n\n"
    return msg + f"```{file_path_with_lines}\n{numbered_content}\n```"

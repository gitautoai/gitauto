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
    **_kwargs,
):
    """
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28

    params:
    - file_path: file path or directory path. Ex) 'src/main.py' or 'src'
    - line_number: specific line number to focus on
    - keyword: keyword to search in the file content
    """
    if line_number is not None and keyword is not None:
        return "Error: You can only specify either line_number or keyword, not both."

    # Convert line_number to int if it's a string
    if line_number is not None and isinstance(line_number, str):
        try:
            line_number = int(line_number)
        except ValueError:
            return f"Error: line_number '{line_number}' is not a valid integer."

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

    # If line_number is specified, show the lines around the line_number
    buffer = 50
    if line_number is not None and line_number > 1 and len(lines) > 100:
        start = max(line_number - buffer, 0)
        end = min(line_number + buffer, len(lines))
        numbered_lines = numbered_lines[start : end + 1]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start + 1}-L{end + 1}"

    # If keyword is specified, show the lines containing the keyword
    elif keyword is not None:
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

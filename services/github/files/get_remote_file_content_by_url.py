import base64

import requests

from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.urls.parse_urls import parse_github_url


@handle_exceptions(default_return_value=("", ""), raise_on_error=False)
def get_remote_file_content_by_url(url: str, token: str):
    """https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28"""
    parts = parse_github_url(url)
    owner, repo, ref, file_path = (
        parts["owner"],
        parts["repo"],
        parts["ref"],
        parts["file_path"],
    )
    start, end = parts["start_line"], parts["end_line"]
    api_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers = create_headers(token=token)
    response = requests.get(url=api_url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    response_json = response.json()
    encoded_content: str = response_json["content"]  # Base64 encoded content
    decoded_content = base64.b64decode(s=encoded_content).decode(encoding=UTF8)
    numbered_lines = [
        f"{i + 1}: {line}" for i, line in enumerate(decoded_content.split("\n"))
    ]

    if start is not None and end is not None:
        numbered_lines = numbered_lines[start - 1 : end]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start}-L{end}"
    elif start is not None:
        numbered_lines = [numbered_lines[start - 1]]  # noqa: E203
        file_path_with_lines = f"{file_path}#L{start}"
    else:
        file_path_with_lines = file_path

    numbered_content = "\n".join(numbered_lines)
    return file_path, f"```{file_path_with_lines}\n{numbered_content}\n```"

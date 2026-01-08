from requests import post

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def render_text(base_args: BaseArgs, text: str) -> str:
    """https://docs.github.com/en/rest/markdown/markdown?apiVersion=2022-11-28#render-a-markdown-document"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    url = f"{GITHUB_API_URL}/markdown"
    headers = create_headers(token=token)
    body = {"text": text, "mode": "gfm", "context": f"{owner}/{repo}"}
    response = post(url=url, headers=headers, json=body, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text

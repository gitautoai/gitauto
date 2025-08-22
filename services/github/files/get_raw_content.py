import base64
import requests
from config import GITHUB_API_URL, TIMEOUT, UTF8
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_raw_content(owner: str, repo: str, file_path: str, ref: str, token: str):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 404:
        return None

    response.raise_for_status()

    res_json = response.json()

    # If it's a directory, return None
    if not isinstance(res_json, dict) or "content" not in res_json:
        return None

    # Decode base64 content
    encoded_content = res_json["content"]
    decoded_content = base64.b64decode(encoded_content).decode(UTF8)

    return decoded_content

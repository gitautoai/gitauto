# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.contents import Contents
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_file_info(
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Get complete file information from GitHub repository."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={new_branch}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    file_info: Contents = response.json()

    # Handle case where response is a list (directory listing) or directory
    if isinstance(file_info, list) or file_info.get("type") == "dir":
        return None

    return file_info

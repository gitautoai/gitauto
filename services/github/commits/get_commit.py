# Standard imports
from typing import cast

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_commit(base_args: BaseArgs, commit_sha: str):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]

    # Get current commit to get tree SHA
    commit_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits/{commit_sha}"
    headers = create_headers(token=token)

    commit_response = requests.get(url=commit_url, headers=headers, timeout=TIMEOUT)
    commit_response.raise_for_status()
    return cast(str, commit_response.json()["tree"]["sha"])

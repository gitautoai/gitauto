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
def create_commit(base_args: BaseArgs, message: str, tree_sha: str, parent_sha: str):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]

    # Create new commit with same tree (empty commit)
    commit_data = {"message": message, "tree": tree_sha, "parents": [parent_sha]}

    new_commit_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits"
    headers = create_headers(token=token)

    new_commit_response = requests.post(
        url=new_commit_url, json=commit_data, headers=headers, timeout=TIMEOUT
    )
    new_commit_response.raise_for_status()
    return cast(str, new_commit_response.json()["sha"])

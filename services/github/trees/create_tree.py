# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_tree(base_args: BaseArgs, base_tree_sha: str, tree_items: list[dict]):
    """https://docs.github.com/en/rest/git/trees#create-a-tree"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees"
    headers = create_headers(token=token)

    tree_data = {"base_tree": base_tree_sha, "tree": tree_items}

    response = requests.post(url=url, json=tree_data, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    sha: str = response.json()["sha"]
    return sha

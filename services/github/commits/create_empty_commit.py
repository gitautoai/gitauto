# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def create_empty_commit(
    base_args: BaseArgs, message: str = "Empty commit to trigger final tests"
):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    branch = base_args["new_branch"]

    # Get current branch reference
    ref_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}"
    headers = create_headers(token=token)

    ref_response = requests.get(url=ref_url, headers=headers, timeout=TIMEOUT)
    ref_response.raise_for_status()
    current_sha = ref_response.json()["object"]["sha"]

    # Get current commit to get tree SHA
    commit_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits/{current_sha}"
    commit_response = requests.get(url=commit_url, headers=headers, timeout=TIMEOUT)
    commit_response.raise_for_status()
    tree_sha = commit_response.json()["tree"]["sha"]

    # Create new commit with same tree (empty commit)
    commit_data = {"message": message, "tree": tree_sha, "parents": [current_sha]}

    new_commit_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits"
    new_commit_response = requests.post(
        url=new_commit_url, json=commit_data, headers=headers, timeout=TIMEOUT
    )
    new_commit_response.raise_for_status()
    new_commit_sha = new_commit_response.json()["sha"]

    # Update branch reference
    update_ref_data = {"sha": new_commit_sha}
    update_ref_response = requests.patch(
        url=ref_url, json=update_ref_data, headers=headers, timeout=TIMEOUT
    )
    update_ref_response.raise_for_status()

    return True

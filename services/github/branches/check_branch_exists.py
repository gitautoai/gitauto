import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_branch_exists(owner: str, repo: str, branch_name: str, token: str):
    """https://docs.github.com/en/rest/branches/branches?apiVersion=2022-11-28#get-a-branch"""
    if not branch_name:
        return False

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{branch_name}"
    headers = create_headers(token=token, media_type="")
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # If the branch does not exist
    if response.status_code == 404:
        return False

    response.raise_for_status()
    return True

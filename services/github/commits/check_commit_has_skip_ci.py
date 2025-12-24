import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_commit_has_skip_ci(owner: str, repo: str, commit_sha: str, token: str):
    headers = create_headers(token)

    response = requests.get(
        f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits/{commit_sha}",
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    commit_data = response.json()
    commit_message = commit_data.get("commit", {}).get("message", "")

    return "[skip ci]" in commit_message

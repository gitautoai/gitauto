import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

NOREPLY_SUFFIX = "@users.noreply.github.com"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_email_from_commits(owner: str, repo: str, username: str, token: str):
    """Fallback: get email from recent commits when the public profile has no email.
    https://docs.github.com/en/rest/commits/commits#list-commits"""
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits",
        headers=create_headers(token=token),
        params={"author": username, "per_page": 5},
        timeout=TIMEOUT,
    )
    if response.status_code == 409:
        logger.info("Repository %s/%s is empty, skipping email lookup", owner, repo)
        return None

    response.raise_for_status()
    commits: list[dict[str, dict[str, dict[str, str]]]] = response.json()
    for commit in commits:
        commit_obj = commit.get("commit")
        if not commit_obj:
            continue
        author = commit_obj.get("author")
        if not author:
            continue
        email = author.get("email")
        if email and not email.endswith(NOREPLY_SUFFIX):
            return email
    return None

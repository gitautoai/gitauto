import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0, raise_on_error=False)
def get_head_commit_count_behind_base(
    owner: str, repo: str, base: str, head: str, token: str
):
    """https://docs.github.com/en/rest/commits/commits#compare-two-commits
    Returns how many commits head is behind base."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/compare/{base}...{head}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    behind_by: int = response.json()["behind_by"]
    logger.info("%s is %d commits behind %s", head, behind_by, base)
    return behind_by

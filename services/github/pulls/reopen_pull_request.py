import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def reopen_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    token: str,
):
    """Reopen a closed PR. Safe to call on already-open PRs — GitHub treats state=open as a no-op.
    https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = create_headers(token=token)
    body = {"state": "open"}

    response = requests.patch(url=url, headers=headers, json=body, timeout=TIMEOUT)
    response.raise_for_status()
    logger.info("Reopened PR #%d", pr_number)
    return True

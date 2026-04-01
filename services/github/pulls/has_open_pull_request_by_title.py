import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.pull_request import PullRequest
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def has_open_pull_request_by_title(owner: str, repo: str, token: str, title: str):
    """Check if an open PR with the given title already exists."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    headers = create_headers(token=token)
    params: dict[str, str | int] = {"state": "open", "per_page": 100}
    response = requests.get(url=url, headers=headers, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    prs: list[PullRequest] = response.json()
    for pr in prs:
        pr_title = pr.get("title")
        if pr_title and title in pr_title:
            logger.info(
                "PR with title '%s' already exists for %s/%s (#%d)",
                title,
                owner,
                repo,
                pr["number"],
            )
            return True

    logger.info("No open PR with title '%s' found for %s/%s", title, owner, repo)
    return False

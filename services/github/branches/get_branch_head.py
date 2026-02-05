import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.branch import Branch
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_branch_head(owner: str, repo: str, branch: str, token: str):
    # https://docs.github.com/en/rest/branches/branches#get-a-branch
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{branch}"
    headers = create_headers(token=token)

    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data: Branch = response.json()

    head_sha = data["commit"]["sha"]
    logger.info("Branch %s head SHA: %s", branch, head_sha)
    return head_sha

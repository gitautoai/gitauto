# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, PER_PAGE, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_pull_request_commits(owner: str, repo: str, pull_number: int, token: str):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/commits"
    headers = create_headers(token=token)
    commits = []
    page = 1

    while True:
        params = {"per_page": PER_PAGE, "page": page}
        response = requests.get(
            url=url, headers=headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        page_commits = response.json()

        if not page_commits:
            break

        commits.extend(page_commits)
        page += 1

    return commits

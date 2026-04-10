# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, PER_PAGE, TIMEOUT
from services.github.types.pull_request_file import PullRequestFile
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_pull_request_files(owner: str, repo: str, pr_number: int, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = create_headers(token=token)
    all_files: list[PullRequestFile] = []
    page = 1

    while True:
        params = {"per_page": PER_PAGE, "page": page}
        response = requests.get(
            url=url, headers=headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        files: list[PullRequestFile] = response.json()

        if not files:
            break

        all_files.extend(files)
        page += 1

    return all_files

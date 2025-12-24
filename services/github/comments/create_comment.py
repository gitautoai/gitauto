import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_comment(
    *,
    owner: str,
    repo: str,
    token: str,
    issue_number: int,
    body: str,
    input_from: str = "github",
):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment"""

    if input_from == "github":
        response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=create_headers(token=token),
            json={"body": body},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        url: str = response.json()["url"]
        return url

    if input_from == "jira":
        return None

    return None

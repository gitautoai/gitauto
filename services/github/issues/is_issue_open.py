import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=True, raise_on_error=False)
def is_issue_open(issue_url: str, token: str) -> bool:
    if not issue_url:
        return False

    # Convert GitHub issue URL to API URL
    # https://github.com/owner/repo/issues/123 -> https://api.github.com/repos/owner/repo/issues/123
    parts = issue_url.replace("https://github.com/", "").split("/")
    if len(parts) < 4 or parts[2] != "issues":
        return True

    owner, repo, _, issue_number = parts[:4]
    api_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}"

    headers = create_headers(token=token)
    response = requests.get(url=api_url, headers=headers, timeout=TIMEOUT)

    # If we can't check the status, assume it's open to avoid duplicates
    if response.status_code != 200:
        return True

    issue_data = response.json()
    return issue_data.get("state") == "open"

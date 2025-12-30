# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.check_suite import CheckSuite
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_check_suites(owner: str, repo: str, ref: str, token: str):
    """https://docs.github.com/en/rest/checks/suites#list-check-suites-for-a-git-reference"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits/{ref}/check-suites"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    check_suites: list[CheckSuite] = data.get("check_suites", [])
    return check_suites

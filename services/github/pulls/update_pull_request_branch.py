# pylint: disable=broad-exception-caught

import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value=("failed", "Unknown error"), raise_on_error=False
)
def update_pull_request_branch(
    owner: str, repo: str, pull_number: int, token: str
) -> tuple[str, str | None]:
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request-branch"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/update-branch"
    headers = create_headers(token=token)
    response = requests.put(url=url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 202:
        return ("updated", None)

    if response.status_code == 422:
        try:
            error_detail = response.json().get("message", "")
            if "no new commits" in error_detail.lower():
                return ("up_to_date", None)
        except Exception:
            pass

    if response.status_code not in [200, 202]:
        error_msg = f"HTTP {response.status_code}"
        try:
            error_detail = response.json().get("message", "")
            if error_detail:
                error_msg += f": {error_detail}"
        except Exception:
            pass
        return ("failed", error_msg)

    return ("updated", None)

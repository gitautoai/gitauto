from typing import Literal

import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions

MergeMethod = Literal["merge", "squash", "rebase"]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def merge_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    token: str,
    merge_method: MergeMethod = "merge",
):
    """https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request"""
    headers = create_headers(token=token)
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/merge"

    data = {"merge_method": merge_method}

    response = requests.put(url=url, headers=headers, json=data, timeout=TIMEOUT)

    if response.status_code == 405:
        error_detail = response.json().get(
            "message", "Branch protection rule preventing merge"
        )
        print(
            f"Branch protection preventing merge for {owner}/{repo} PR #{pull_number}: {error_detail}"
        )
        return {"code": 405, "message": error_detail}

    response.raise_for_status()

    return {"code": 200, "message": ""}

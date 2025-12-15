import requests
from config import GITHUB_API_URL, GITHUB_APP_USER_NAME, PER_PAGE, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_open_pull_requests(owner: str, repo: str, target_branch: str, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    headers = create_headers(token=token)
    pull_requests: list[dict] = []
    page = 1

    while True:
        params = {
            "base": target_branch,
            "state": "open",
            "per_page": PER_PAGE,
            "page": page,
        }
        response = requests.get(
            url=url, headers=headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        prs = response.json()

        if not prs:
            break

        gitauto_prs = [
            pr
            for pr in prs
            if pr.get("user", {}).get("login", "").lower()
            == GITHUB_APP_USER_NAME.lower()
        ]
        pull_requests.extend(gitauto_prs)
        page += 1

    return pull_requests

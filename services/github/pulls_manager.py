import requests
from config import GITHUB_API_URL, TIMEOUT, PER_PAGE
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from services.github.user_manager import check_user_is_collaborator
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_reviewers(base_args: BaseArgs):
    """https://docs.github.com/en/rest/pulls/review-requests?apiVersion=2022-11-28#request-reviewers-for-a-pull-request"""
    owner, repo, pr_number, token, reviewers = (
        base_args["owner"],
        base_args["repo"],
        base_args["pr_number"],
        base_args["token"],
        base_args["reviewers"],
    )

    # Check if the reviewers are collaborators because reviewers must be collaborators
    valid_reviewers: list[str] = []
    for reviewer in reviewers:
        is_collaborator = check_user_is_collaborator(
            owner=owner, repo=repo, user=reviewer, token=token
        )
        if is_collaborator:
            valid_reviewers.append(reviewer)

    # If no valid reviewers, return
    if not valid_reviewers:
        return

    # Add the reviewers to the pull request
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
    headers = create_headers(token=token)
    json = {"reviewers": valid_reviewers}
    response = requests.post(url=url, headers=headers, json=json, timeout=TIMEOUT)
    response.raise_for_status()


@handle_exceptions(default_return_value=("", ""), raise_on_error=False)
def get_pull_request(url: str, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request"""
    headers = create_headers(token=token)
    res = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    res.raise_for_status()
    res_json = res.json()
    title: str = res_json["title"]
    body: str = res_json["body"]
    return title, body


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_pull_request_files(url: str, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files"""
    headers = create_headers(token=token)
    changes: list[dict[str, str]] = []
    page = 1
    while True:
        params = {"per_page": PER_PAGE, "page": page}
        response = requests.get(
            url=url, headers=headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        files = response.json()
        if not files:
            break
        for file in files:
            if "patch" not in file:
                continue
            filename, status, patch = file["filename"], file["status"], file["patch"]
            changes.append({"filename": filename, "status": status, "patch": patch})
        page += 1
    return changes

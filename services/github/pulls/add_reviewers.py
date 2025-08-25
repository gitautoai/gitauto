import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.github.types.github_types import BaseArgs
from services.github.collaborators.check_user_is_collaborator import (
    check_user_is_collaborator,
)
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_reviewers(base_args: BaseArgs):
    """https://docs.github.com/en/rest/pulls/review-requests?apiVersion=2022-11-28#request-reviewers-for-a-pull-request"""
    owner, repo, pr_number, token, reviewers = (
        base_args["owner"],
        base_args["repo"],
        base_args.get("pr_number"),
        base_args["token"],
        base_args["reviewers"],
    )

    if not pr_number:
        raise ValueError("pr_number is required for add_reviewers")

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
    print(f"Adding reviewers: {valid_reviewers}")

    # Add the reviewers to the pull request
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
    headers = create_headers(token=token)
    json = {"reviewers": valid_reviewers}
    response = requests.post(url=url, headers=headers, json=json, timeout=TIMEOUT)
    response.raise_for_status()

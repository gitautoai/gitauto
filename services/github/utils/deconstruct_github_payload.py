# Standard library imports
from datetime import datetime
from random import choices
from string import ascii_letters, digits
from typing import cast

# Local imports
from config import PRODUCT_ID, ISSUE_NUMBER_FORMAT, GITHUB_APP_USER_ID
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.issues.get_parent_issue import get_parent_issue
from services.github.types.github_types import BaseArgs, GitHubLabeledPayload
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_user_public_email import get_user_public_email
from services.github.commits.get_latest_remote_commit_sha import get_latest_remote_commit_sha
from services.supabase.repositories.get_repository import get_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.urls.extract_urls import extract_urls


@handle_exceptions(default_return_value=(None, None), raise_on_error=True)
def deconstruct_github_payload(
    payload: GitHubLabeledPayload,
):
    # Extract issue related variables
    issue = payload["issue"]
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_body = issue["body"] or ""
    issuer_name = issue["user"]["login"]

    # Extract repository related variables
    repo = payload["repository"]
    repo_id = repo["id"]
    repo_name = repo["name"]
    clone_url = repo["clone_url"]
    is_fork = repo.get("fork", False)

    # Extract owner related variables
    owner_type = repo["owner"]["type"]
    owner_name = repo["owner"]["login"]
    owner_id = repo["owner"]["id"]

    # Extract branch related variables
    base_branch_name = repo["default_branch"]  # like "main"

    # Get installation access token
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        raise ValueError(
            f"Installation access token is not found for {owner_name}/{repo_name}"
        )

    # Get repository rules from Supabase
    repo_settings = get_repository(repo_id=repo_id)
    target_branch = (
        cast(str | None, repo_settings.get("target_branch")) if repo_settings else None
    )

    # If target branch is set and exists in the repository, use it, otherwise use default branch
    if target_branch and check_branch_exists(
        owner=owner_name, repo=repo_name, branch_name=target_branch, token=token
    ):
        base_branch_name = target_branch
        print(f"Using target branch: {target_branch}")

    date = datetime.now().strftime(format="%Y%m%d")  # like "20241224"
    time = datetime.now().strftime(format="%H%M%S")  # like "120000" means 12:00:00
    # like "ABCD", "1234", "a1b2"
    random_str = "".join(choices(ascii_letters + digits, k=4))
    new_branch_name = (
        f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}-{random_str}"
    )

    # Extract sender related variables
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]
    is_automation = sender_id == GITHUB_APP_USER_ID
    reviewers = list(
        set(name for name in (sender_name, issuer_name) if "[bot]" not in name)
    )

    # Extract other information
    github_urls, other_urls = extract_urls(text=issue_body)
    sender_email = get_user_public_email(username=sender_name, token=token)

    # Set latest commit SHA to empty (fetched later in handler) and issue comments (empty for GitHub as they're fetched separately)
    latest_commit_sha = ""
    issue_comments: list[str] = []  # GitHub comments are fetched separately in the handler

    # Extract its parent issue
    parent_issue = get_parent_issue(
        owner=owner_name,
        repo=repo_name,
        issue_number=issue_number,
        token=token,
    )
    parent_issue_number = (
        cast(int, parent_issue.get("number")) if parent_issue else None
    )
    parent_issue_title = cast(str, parent_issue.get("title")) if parent_issue else None
    parent_issue_body = cast(str, parent_issue.get("body")) if parent_issue else None

    base_args: BaseArgs = {
        "input_from": "github",
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": clone_url,
        "is_fork": is_fork,
        "issue_number": issue_number,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issuer_name": issuer_name,
        "issue_comments": issue_comments,
        "latest_commit_sha": latest_commit_sha,
        "parent_issue_number": parent_issue_number,
        "parent_issue_title": parent_issue_title,
        "parent_issue_body": parent_issue_body,
        "base_branch": base_branch_name,
        "new_branch": new_branch_name,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "is_automation": is_automation,
        "reviewers": reviewers,
        "github_urls": github_urls,
        "other_urls": other_urls,
    }

    return base_args, repo_settings

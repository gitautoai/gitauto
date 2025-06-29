# Standard imports
from datetime import datetime
from typing import Any

# Local imports
from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.branches.get_default_branch import get_default_branch
from services.github.types.github_types import BaseArgs
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.token.get_installation_token import get_installation_access_token
from services.supabase.installations_manager import get_installation_info
from services.supabase.repositories.get_repository import get_repository_settings
from utils.error.handle_exceptions import handle_exceptions
from utils.urls.extract_urls import extract_urls


@handle_exceptions(default_return_value=(None, None), raise_on_error=True)
def deconstruct_jira_payload(
    payload: dict[str, Any],
) -> tuple[BaseArgs | None]:
    """Extract and format base arguments and related metadata from Jira payload."""
    # Extract issue related variables
    issue: dict[str, Any] = payload["issue"]
    issue_number: int = issue["id"]  # Jira issue ID NOT GitHub issue number
    issue_title: str = issue["title"]  # Jira issue title NOT GitHub issue title
    issue_body: str = issue["body"]  # Jira issue body NOT GitHub issue body
    issue_comments: list[dict[str, Any]] = issue["comments"]  # Jira issue comments

    # Extract issuer related variables
    issuer: dict[str, Any] = payload["creator"]
    issuer_id: str = issuer["id"]  # Jira account ID NOT GitHub user ID
    issuer_name: str = issuer["displayName"]  # Jira Display Name NOT GitHub username
    issuer_email: str = issuer["email"]

    # Extract repository related variables
    repo: dict[str, Any] = payload["repo"]
    repo_id: int = repo["id"]
    repo_name: str = repo["name"]

    # Extract owner related variables
    owner: dict[str, Any] = payload["owner"]
    owner_name: str = owner["name"]
    installation_id, owner_id, owner_type = get_installation_info(owner_name=owner_name)
    token: str = get_installation_access_token(installation_id=installation_id)
    is_fork: bool = is_repo_forked(owner=owner_name, repo=repo_name, token=token)

    # Extract branch related variables
    base_branch_name, latest_commit_sha = get_default_branch(
        owner=owner_name, repo=repo_name, token=token
    )

    # Get repository rules from Supabase
    repo_settings = get_repository_settings(repo_id=repo_id)
    if repo_settings:
        target_branch = repo_settings.get("target_branch")
    else:
        target_branch = None

    # If target branch is set and exists in the repository, use it, otherwise use default branch
    if target_branch and check_branch_exists(
        owner=owner_name, repo=repo_name, branch_name=target_branch, token=token
    ):
        base_branch_name = target_branch

    date: str = datetime.now().strftime(format="%Y%m%d")  # like "20241224"
    time: str = datetime.now().strftime(format="%H%M%S")  # like "120000" means 12:00:00
    new_branch_name = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}"

    # Extract sender related variables
    sender_id: int = issuer_id
    sender_name = issuer_name
    sender_email = issuer_email
    is_automation = False
    reviewers: list[str] = []

    # Extract other information
    github_urls, other_urls = extract_urls(text=issue_body)

    base_args: BaseArgs = {
        "input_from": "jira",
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": "",
        "is_fork": is_fork,
        "issue_number": issue_number,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issue_comments": issue_comments,
        "issuer_name": issuer_name,
        "issuer_email": issuer_email,
        "base_branch": base_branch_name,
        "latest_commit_sha": latest_commit_sha,
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

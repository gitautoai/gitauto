# Standard imports
from datetime import datetime
from typing import cast

# Local imports
from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.branches.get_default_branch import get_default_branch
from services.github.repositories.is_repo_forked import is_repo_forked
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.owner import OwnerType
from services.jira.types import JiraPayload
from services.supabase.installations.get_installation import get_installation
from services.supabase.repositories.get_repository import get_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.urls.extract_urls import extract_urls


@handle_exceptions(default_return_value=(None, None), raise_on_error=True)
def deconstruct_jira_payload(payload: JiraPayload):
    """Extract and format base arguments and related metadata from Jira payload."""
    # Extract issue related variables
    issue = payload["issue"]
    issue_number = issue["id"]  # Jira issue ID NOT GitHub issue number
    issue_title = issue["title"]  # Jira issue title NOT GitHub issue title
    issue_body = issue["body"]  # Jira issue body NOT GitHub issue body
    issue_comments = issue["comments"]  # Jira issue comments

    # Extract issuer related variables
    issuer = payload["creator"]
    issuer_id = issuer["id"]  # Jira account ID NOT GitHub user ID
    issuer_name = issuer["displayName"]  # Jira Display Name NOT GitHub username
    issuer_email = issuer["email"]

    # Extract repository related variables
    repo = payload["repo"]
    repo_id = repo["id"]
    repo_name = repo["name"]

    # Extract owner related variables
    owner = payload["owner"]
    owner_id = owner["id"]
    owner_name = owner["name"]

    # Get installation info
    installation = get_installation(owner_id=owner_id)
    if not installation:
        raise ValueError(f"Installation not found for owner_id: {owner_id}")

    installation_id = cast(int, installation["installation_id"])
    owner_type = cast(OwnerType, installation["owner_type"])
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        raise ValueError(f"Failed to get token for installation_id: {installation_id}")
    is_fork = is_repo_forked(owner=owner_name, repo=repo_name, token=token)

    # Extract branch related variables
    base_branch_name, latest_commit_sha = get_default_branch(
        owner=owner_name, repo=repo_name, token=token
    )

    # Get repository rules from Supabase
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    target_branch = (
        cast(str | None, repo_settings["target_branch"]) if repo_settings else None
    )

    # If target branch is set and exists in the repository, use it, otherwise use default branch
    if target_branch and check_branch_exists(
        owner=owner_name, repo=repo_name, branch_name=target_branch, token=token
    ):
        base_branch_name = target_branch

    date = datetime.now().strftime(format="%Y%m%d")  # like "20241224"
    time = datetime.now().strftime(format="%H%M%S")  # like "120000" means 12:00:00
    new_branch_name = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}"

    # Extract sender related variables
    sender_id = issuer_id
    sender_name = issuer_name
    sender_email = issuer_email
    is_automation = False
    reviewers: list[str] = []

    # Extract other information
    github_urls, other_urls = extract_urls(text=issue_body)

    base_args = {
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

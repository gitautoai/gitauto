# Standard library imports
from datetime import datetime
from typing import Literal

# Local imports
from config import PRODUCT_ID, ISSUE_NUMBER_FORMAT, GITHUB_APP_USER_ID
from services.github.branch_manager import check_branch_exists
from services.github.github_types import (
    BaseArgs,
    GitHubLabeledPayload,
    IssueInfo,
    RepositoryInfo,
)
from services.github.github_manager import (
    get_installation_access_token,
    get_user_public_email,
)
from services.github.issues_manager import get_parent_issue
from services.supabase.repository_manager import get_repository_rules
from utils.error.handle_exceptions import handle_exceptions
from utils.urls.extract_urls import extract_urls


def create_permission_url(
    owner_type: Literal["Organization", "User"], owner_name: str, installation_id: int
):
    url_base = "https://github.com"
    url_part = f"settings/installations/{installation_id}/permissions/update"
    if owner_type == "Organization":
        return f"{url_base}/organizations/{owner_name}/{url_part}"
    return f"{url_base}/{url_part}"


@handle_exceptions(default_return_value={}, raise_on_error=True)
def deconstruct_github_payload(payload: GitHubLabeledPayload):
    """Extract and format base arguments and related metadata from GitHub payload."""
    # Extract issue related variables
    issue: IssueInfo = payload["issue"]
    issue_number: int = issue["number"]
    issue_title: str = issue["title"]
    issue_body: str = issue["body"] or ""
    issuer_name: str = issue["user"]["login"]

    # Extract repository related variables
    repo: RepositoryInfo = payload["repository"]
    repo_id: int = repo["id"]
    repo_name: str = repo["name"]
    clone_url: str = repo["clone_url"]
    is_fork: bool = repo.get("fork", False)

    # Extract owner related variables
    owner_type: Literal["Organization", "User"] = repo["owner"]["type"]
    owner_name: str = repo["owner"]["login"]
    owner_id: int = repo["owner"]["id"]

    # Extract branch related variables
    base_branch_name: str = repo["default_branch"]  # like "main"

    # Get installation access token
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get repository rules from Supabase
    repo_rules = get_repository_rules(repo_id=repo_id)
    print(f"Repo rules: {repo_rules}")
    if repo_rules:
        target_branch = repo_rules.get("target_branch")
        print(f"Target branch: {target_branch}")
    else:
        target_branch = None

    # If target branch is set and exists in the repository, use it, otherwise use default branch
    if target_branch and check_branch_exists(
        owner=owner_name, repo=repo_name, branch_name=target_branch, token=token
    ):
        base_branch_name = target_branch
        print(f"Using target branch: {target_branch}")

    date: str = datetime.now().strftime(format="%Y%m%d")  # like "20241224"
    time: str = datetime.now().strftime(format="%H%M%S")  # like "120000" means 12:00:00
    new_branch_name = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}"

    # Extract sender related variables
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    is_automation: bool = sender_id == GITHUB_APP_USER_ID
    reviewers: list[str] = list(
        set(name for name in (sender_name, issuer_name) if "[bot]" not in name)
    )

    # Extract other information
    github_urls, other_urls = extract_urls(text=issue_body)
    sender_email: str = get_user_public_email(username=sender_name, token=token)

    # Extract its parent issue
    parent_issue = get_parent_issue(
        owner=owner_name,
        repo=repo_name,
        issue_number=issue_number,
        token=token,
    )
    parent_issue_number: int | None = (
        parent_issue.get("number") if parent_issue else None
    )
    parent_issue_title: str | None = parent_issue.get("title") if parent_issue else None
    parent_issue_body: str | None = parent_issue.get("body") if parent_issue else None

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

    return base_args

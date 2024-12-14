# Standard library imports
from datetime import datetime
from typing import Literal

# Local imports
from config import PRODUCT_ID, ISSUE_NUMBER_FORMAT, GITHUB_APP_USER_ID
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
from utils.extract_urls import extract_urls
from utils.handle_exceptions import handle_exceptions


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
    repo_name: str = repo["name"]
    clone_url: str = repo["clone_url"]
    is_fork: bool = repo.get("fork", False)

    # Extract owner related variables
    owner_type: Literal["Organization", "User"] = repo["owner"]["type"]
    owner_name: str = repo["owner"]["login"]
    owner_id: int = repo["owner"]["id"]

    # Extract branch related variables
    base_branch_name: str = repo["default_branch"]  # like "main"
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
    # print(f"github_urls: {github_urls}")
    # print(f"other_urls: {other_urls}")
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)
    sender_email: str = get_user_public_email(username=sender_name, token=token)

    base_args: BaseArgs = {
        "input_from": "github",
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "clone_url": clone_url,
        "is_fork": is_fork,
        "issue_number": issue_number,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issuer_name": issuer_name,
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

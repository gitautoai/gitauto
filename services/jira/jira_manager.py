# Standard imports
from datetime import datetime
from json import dumps
from typing import Any

# Third party imports
from fastapi import HTTPException, Request

# Local imports
from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
from services.github.branch_manager import get_default_branch
from services.github.github_manager import get_installation_access_token
from services.github.github_types import BaseArgs
from services.github.repo_manager import is_repo_forked
from services.supabase.installations_manager import get_installation_info
from utils.extract_urls import extract_urls
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def verify_jira_webhook(request: Request):
    """Verify that the request came from Atlassian Forge"""
    print("Request Headers:", dumps(dict(request.headers), indent=2))

    # Verify that the request came from Atlassian Forge
    if request.headers.get("atl-edge-tenant") != "forge-outbound-proxy":
        print("Not a Forge request")
        raise HTTPException(status_code=401, detail="Request not from Forge")

    payload = await request.json()
    # print("Payload:", json.dumps(payload, indent=2))
    return payload


@handle_exceptions(default_return_value={}, raise_on_error=True)
def deconstruct_jira_payload(payload: dict[str, Any]):
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

    return base_args

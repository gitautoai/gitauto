# Standard library imports
from typing import cast

# Local imports
from config import GITHUB_APP_USER_ID
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.types.github_types import BaseArgs, PrLabeledPayload
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_user_public_email import get_user_public_info
from services.supabase.repositories.get_repository import get_repository
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.urls.extract_urls import extract_urls


@handle_exceptions(default_return_value=(None, None), raise_on_error=True)
def deconstruct_github_payload(
    payload: PrLabeledPayload,
):
    # Extract PR related variables (payload is from pull_request.labeled webhook)
    pr = payload["pull_request"]
    pr_number = pr["number"]
    pr_title = pr["title"]
    pr_body = pr["body"] or ""
    pr_creator = pr["user"]["login"]
    new_branch_name = pr["head"]["ref"]
    assignees = pr.get("assignees", [])
    assignee_names = [a["login"] for a in assignees]

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
        logger.info("Using target branch: %s", target_branch)

    # Extract sender related variables
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]
    is_automation = sender_id == GITHUB_APP_USER_ID

    # Build reviewers from sender, PR creator, and PR assignees (for schedule triggers where both sender and creator are bots, assignees provide the human reviewer)
    reviewers = list(
        set(
            name
            for name in (*assignee_names, sender_name, pr_creator)
            if "[bot]" not in name
        )
    )

    # Extract other information
    github_urls, other_urls = extract_urls(text=pr_body)
    sender_info = get_user_public_info(username=sender_name, token=token)
    sender_email = sender_info.email
    sender_display_name = sender_info.display_name

    base_args: BaseArgs = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": clone_url,
        "is_fork": is_fork,
        "pr_number": pr_number,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "pr_comments": [],
        "pr_creator": pr_creator,
        "base_branch": base_branch_name,
        "new_branch": new_branch_name,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "sender_display_name": sender_display_name,
        "is_automation": is_automation,
        "reviewers": reviewers,
        "github_urls": github_urls,
        "other_urls": other_urls,
        "clone_dir": "",
    }

    return base_args, repo_settings

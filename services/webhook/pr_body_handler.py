# Third-party imports
from json import dumps

# Local imports
from config import GITHUB_APP_USER_NAME

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.pulls.update_pull_request_body import update_pull_request_body
from services.github.token.get_installation_token import get_installation_access_token

# Local imports (OpenAI)
from services.openai.chat import chat_with_ai
from utils.logging.logging_config import logger
from utils.prompts.write_pr_body import WRITE_PR_BODY


def write_pr_description(payload: dict):
    # Handle None or empty payload
    if not payload:
        return

    # Check if required keys exist
    if (
        "pull_request" not in payload
        or "repository" not in payload
        or "installation" not in payload
    ):
        return

    # Return if the author of the pull request is not GitAuto itself
    pull: dict = payload["pull_request"]
    if pull["user"]["login"] != GITHUB_APP_USER_NAME:
        return

    # Get the basic information
    repo: dict = payload["repository"]
    owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]
    installation_id: int = payload["installation"]["id"]
    token = get_installation_access_token(installation_id)

    # Get the pull request information
    pr_title: str = pull["title"]
    pr_number: int = pull["number"]
    pr_body_raw: str = pull["body"]
    # Handle None pr_body_raw
    if pr_body_raw is None:
        pr_body_raw = ""

    pr_url: str = pull["url"]
    pr_files_url = pr_url + "/files"
    head_branch: str = pull["head"]["ref"]

    # Schedule PRs and dashboard PRs don't need body rewriting - skip
    if "/schedule-" in head_branch or "/dashboard-" in head_branch:
        return

    # Get the pull request file changes
    file_changes = get_pull_request_file_changes(url=pr_files_url, token=token)

    # Parse git commands from the body
    commands = []
    for line in pr_body_raw.split("\n"):
        if line.startswith("git "):
            commands.append(line)

    # Create an input object
    user_input = dumps(
        {
            "owner": owner,
            "repo": repo_name,
            "pr_title": pr_title,
            "pr_body": pr_body_raw,
            "file_changes": file_changes,
        }
    )

    # Safety check: Stop if PR is closed or branch is deleted before AI call
    if not is_pull_request_open(
        owner=owner, repo=repo_name, pr_number=pr_number, token=token
    ):
        logger.info("Skipping AI call: PR #%d has been closed", pr_number)
        return

    if not check_branch_exists(
        owner=owner, repo=repo_name, branch_name=head_branch, token=token
    ):
        logger.info("Skipping AI call: Branch '%s' has been deleted", head_branch)
        return

    # Write a PR description
    pr_body = chat_with_ai(
        system_input=WRITE_PR_BODY,
        user_input=user_input,
    )

    # Add commands at the end
    pr_body = pr_body + "\n\n" + "```\n" + "\n".join(commands) + "\n```"

    # Update the PR with the PR description
    update_pull_request_body(url=pr_url, token=token, body=pr_body)

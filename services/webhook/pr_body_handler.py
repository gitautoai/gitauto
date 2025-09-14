# Third-party imports
from json import dumps

# Local imports
from config import GITHUB_APP_USER_NAME

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.issues.get_issue_body import get_issue_body
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.pulls.update_pull_request_body import update_pull_request_body
from services.github.token.get_installation_token import get_installation_access_token

# Local imports (OpenAI)
from services.openai.chat import chat_with_ai
from utils.prompts.write_pr_body import WRITE_PR_BODY


def write_pr_description(payload: dict):
    # Handle None or empty payload
    if not payload:
        return
    
    # Check if required keys exist
    if "pull_request" not in payload or "repository" not in payload or "installation" not in payload:
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
    token: str = get_installation_access_token(installation_id)

    # Get the pull request information
    pull_title: str = pull["title"]
    if pull_title.startswith("GitAuto: "):
        pull_title = pull_title[9:]  # Remove "GitAuto: " prefix
    pull_number: int = pull["number"]
    pull_body: str = pull["body"]
    pull_url: str = pull["url"]
    pull_files_url = pull_url + "/files"
    head_branch: str = pull["head"]["ref"]

    # Get the pull request file changes
    file_changes = get_pull_request_file_changes(url=pull_files_url, token=token)

    # Extract issue number from "Resolves #<issue_number>"
    issue_number = None
    issue_body = None
    resolves_statement = None
    commands = []

    # Parse the body line by line
    for line in pull_body.split("\n"):
        if line.startswith("Resolves #"):
            issue_number = int(line.split("#")[1])
            resolves_statement = line
        elif line.startswith("git "):
            commands.append(line)

    # Get the issue title and body
    if issue_number is not None:
        issue_body: str | None = get_issue_body(
            owner=owner, repo=repo_name, issue_number=issue_number, token=token
        )

    # Create an input object
    user_input = dumps(
        {
            "owner": owner,
            "repo": repo_name,
            "issue_title": pull_title,
            "issue_body": issue_body or "",
            "file_changes": file_changes,
        }
    )

    # Safety check: Stop if PR is closed or branch is deleted before AI call
    if not is_pull_request_open(
        owner=owner, repo=repo_name, pull_number=pull_number, token=token
    ):
        print(f"Skipping AI call: PR #{pull_number} has been closed")
        return

    if not check_branch_exists(
        owner=owner, repo=repo_name, branch_name=head_branch, token=token
    ):
        print(f"Skipping AI call: Branch '{head_branch}' has been deleted")
        return

    # Write a PR description to the issue
    pr_body = chat_with_ai(
        system_input=WRITE_PR_BODY,
        user_input=user_input,
    )

    # Add a resolves statement if this PR comes from an GitHub issue
    if resolves_statement:
        pr_body = resolves_statement + "\n\n" + pr_body

    # Add commands at the end
    pr_body = pr_body + "\n\n" + "```\n" + "\n".join(commands) + "\n```"

    # Update the PR with the PR description
    update_pull_request_body(url=pull_url, token=token, body=pr_body)

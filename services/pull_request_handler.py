# Third-party imports
from json import dumps

# Local imports
from config import GITHUB_APP_USER_NAME
from services.github.github_manager import get_installation_access_token
from services.github.issues_manager import get_issue_body
from services.github.pulls_manager import (
    get_pull_request_file_changes,
    update_pull_request_body,
)
from services.openai.chat import chat_with_ai
from services.openai.instructions.write_pr_body import WRITE_PR_BODY


def write_pr_description(payload: dict):
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
    pull_body: str = pull["body"]
    pull_url: str = pull["url"]
    pull_files_url = pull_url + "/files"

    # Get the pull request file changes
    file_changes = get_pull_request_file_changes(url=pull_files_url, token=token)
    print(dumps(file_changes, indent=2))

    # Extract issue number from "Resolves #<issue_number>"
    issue_number = None
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

    # Write a PR description to the issue
    pr_body = chat_with_ai(
        system_input=WRITE_PR_BODY,
        user_input=user_input,
    )
    pr_body = (
        resolves_statement
        + "\n\n"
        + pr_body
        + "\n\n"
        + "```\n"
        + "\n".join(commands)
        + "\n```"
    )

    # Update the PR with the PR description
    update_pull_request_body(url=pull_url, token=token, body=pr_body)

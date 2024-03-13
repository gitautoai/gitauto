# Standard imports
import json
import time
from uuid import uuid4

# Local imports
from config import PRODUCT_ID, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.github.github_manager import (
    commit_changes_to_remote_branch,
    create_pull_request,
    create_remote_branch,
    get_installation_access_token,
    get_issue_comments,
    get_latest_remote_commit_sha,
    get_remote_file_tree,
    create_comment,
    update_comment,
    add_reaction_to_issue,
    create_gitauto_issue_trigger_comment,
)
from services.github.github_types import (
    GitHubEventPayload,
    GitHubInstallationPayload,
    GitHubLabeledPayload,
    IssueInfo,
    RepositoryInfo,
)
from services.openai.chat import write_pr_body
from services.openai.agent import run_assistant
from services.supabase.supabase_manager import InstallationTokenManager
from utils.file_manager import extract_file_name

# Initialize managers
supabase_manager = InstallationTokenManager(
    url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY
)


async def handle_installation_created(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    owner_name: str = payload["installation"]["account"]["login"]

    supabase_manager.save_installation_token(
        installation_id=installation_id,
        owner_name=owner_name,
    )


async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id=installation_id)


async def handle_gitauto(payload: GitHubLabeledPayload, type: str) -> None:
    # Extract label and validate it
    if type == "label" and payload["label"]["name"] != PRODUCT_ID:
        return

    # Extract information from the payload
    issue: IssueInfo = payload["issue"]
    issue_title: str = issue["title"]
    issue_body: str = issue["body"] or ""
    issue_number: int = issue["number"]
    installation_id: int = payload["installation"]["id"]
    repo: RepositoryInfo = payload["repository"]
    owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]
    base_branch: str = repo["default_branch"]

    supabase_manager.increment_request_count(installation_id=installation_id)
    token: str = get_installation_access_token(installation_id=installation_id)
    add_reaction_to_issue(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        content="eyes",
        token=token,
    )

    # Start progress and check if current issue is already in progress from another invocation
    unique_issue_id = f"{owner}/{repo_name}#{issue_number}"
    if not supabase_manager.save_progress_started(
        unique_issue_id=unique_issue_id, installation_id=installation_id
    ):
        create_comment(
            owner=owner,
            repo=repo_name,
            issue_number=issue_number,
            body="The issue is already in progress. Please wait for the previous request to complete.",
            token=token,
        )
        return {"message": "The issue is already in progress."}
    comment_url = create_comment(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        body="![X](https://progress-bar.dev/0/?title=Progress&width=800)\nGitAuto just stared crafting a pull request.",
        token=token,
    )["url"]
    # Prepare contents for Agent
    file_paths: list[str] = get_remote_file_tree(
        owner=owner,
        repo=repo_name,
        ref=base_branch,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    issue_comments: list[str] = get_issue_comments(
        owner=owner, repo=repo_name, issue_number=issue_number, token=token
    )
    pr_body: str = write_pr_body(
        input_message=json.dumps(
            obj={
                "issue_title": issue_title,
                "issue_body": issue_body,
                "issue_comments": issue_comments,
            }
        )
    )
    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Installation token received.\n"
    )

    diffs: list[str] = run_assistant(
        file_paths=file_paths,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        owner=owner,
        pr_body=pr_body,
        ref=base_branch,
        repo=repo_name,
        token=token,
    )

    supabase_manager.update_progress(unique_issue_id=unique_issue_id, progress=50)
    update_comment(
        comment_url=comment_url,
        token=token,
        body="![X](https://progress-bar.dev/50/?title=Progress&width=800)\nHalf way there!",
    )

    # Create a remote branch
    uuid: str = str(object=uuid4())
    new_branch: str = f"{PRODUCT_ID}/issue-#{issue['number']}-{uuid}"
    latest_commit_sha: str = get_latest_remote_commit_sha(
        owner=owner,
        repo=repo_name,
        branch=base_branch,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    create_remote_branch(
        branch_name=new_branch,
        owner=owner,
        repo=repo_name,
        sha=latest_commit_sha,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Remote branch created: {new_branch}.\n"
    )

    # Commit the changes to the new remote branch
    for diff in diffs:
        file_path: str = extract_file_name(diff_text=diff)
        print(
            f"{time.strftime('%H:%M:%S', time.localtime())} File path: {file_path}.\n"
        )
        commit_changes_to_remote_branch(
            branch=new_branch,
            commit_message=f"Update {file_path}",
            diff_text=diff,
            file_path=file_path,
            owner=owner,
            repo=repo_name,
            comment_url=comment_url,
            unique_issue_id=unique_issue_id,
            token=token,
        )
        print(
            f"{time.strftime('%H:%M:%S', time.localtime())} Changes committed to {new_branch}.\n"
        )

    # Create a pull request to the base branch
    issue_link: str = f"Original issue: [#{issue_number}]({issue['html_url']})\n\n"
    if pr_body[:3] == "```\n":
        pr_body = pr_body[4:]
    if pr_body.endswith("```"):
        pr_body = pr_body[:-3]
    git_commands = (
        f"\n\n```\ngit checkout -b {new_branch}\ngit pull origin {new_branch}\n```"
    )
    pull_request_url = create_pull_request(
        base=base_branch,
        body=issue_link + pr_body + git_commands,
        head=new_branch,
        owner=owner,
        repo=repo_name,
        title=f"Fix {issue_title} with {PRODUCT_ID} model",
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )["html_url"]
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Pull request created.\n")

    update_comment(
        comment_url=comment_url,
        token=token,
        body=f"Pull request completed! Check it out here {pull_request_url} 🚀",
    )

    supabase_manager.increment_completed_count(installation_id=installation_id)
    supabase_manager.update_progress(unique_issue_id=unique_issue_id, progress=100)
    return


async def handle_webhook_event(event_name: str, payload: GitHubEventPayload) -> None:
    """Determine the event type and call the appropriate handler"""
    action: str = payload.get("action")
    if not action:
        return

    # Check the type of webhook event and handle accordingly
    if event_name == "installation" and action in ("created", "added"):
        print("Installaton is created")
        await handle_installation_created(payload=payload)

    elif event_name == "installation" and action in ("deleted", "removed"):
        print("Installaton is deleted")
        await handle_installation_deleted(payload=payload)

    elif event_name == "issues":
        if action == "labeled":
            print("Issue is labeled")
            await handle_gitauto(payload=payload, type="label")
        elif action == "opened":
            create_gitauto_issue_trigger_comment(payload=payload)

    elif event_name == "issue_comment" and action == "edited":
        if (
            payload["comment"]["body"] == "- [x] Generate PR"
            or payload["comment"]["body"]
            == "Welcome to GitAuto! 🎉\r\nAfter you create your issue, click the checkbox below to generate a PR!\r\n- [x] Generate PR"
        ):
            print("Issue is labeled")
            await handle_gitauto(payload=payload, type="comment")
        else:
            print("Edit is not an activated GitAtuo trigger.")
            print("VALUE: ", payload["comment"]["body"])

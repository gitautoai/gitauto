# Standard imports
import shutil
import tempfile
from typing import Any

# Local imports
from config import (
    GITHUB_CHECK_RUN_FAILURES,
    PRODUCT_ID,
    PR_BODY_STARTS_WITH,
    ISSUE_NUMBER_FORMAT,
)
from services.check_run_handler import handle_check_run
from services.coverage_analyzer.coverage_analyzer import handle_workflow_coverage
from services.git.git_manager import clone_repo
from services.gitauto_handler import handle_gitauto
from services.github.actions_manager import cancel_workflow_runs_in_progress
from services.github.github_manager import (
    create_comment_on_issue_with_gitauto_button,
    get_installation_access_token,
    get_user_public_email,
)
from services.github.github_types import GitHubInstallationPayload
from services.github.repo_manager import get_repository_stats
from services.pull_request_handler import write_pr_description
from services.review_run_handler import handle_review_run
from services.screenshot_handler import handle_screenshot_comparison
from services.supabase.gitauto_manager import (
    create_installation,
    delete_installation,
    set_issue_to_merged,
)
from services.supabase.repositories_manager import create_or_update_repository
from utils.handle_exceptions import handle_exceptions


def process_repositories(
    owner_name: str,
    owner_id: int,
    repositories: list[dict[str, Any]],
    token: str,
    created_by: str,
    updated_by: str,
) -> None:
    for repo in repositories:
        repo_id = repo["id"]
        repo_name = repo["name"]

        # Create a temporary directory to clone the repository
        temp_dir = tempfile.mkdtemp()
        try:
            print(f"Cloning repository {repo_name} into {temp_dir}")
            clone_repo(
                owner=owner_name, repo=repo_name, token=token, target_dir=temp_dir
            )

            stats = get_repository_stats(local_path=temp_dir)
            print(f"Repository {repo_name} stats: {stats}")

            # Create repository record in Supabase
            create_or_update_repository(
                owner_id=owner_id,
                repo_id=repo_id,
                repo_name=repo_name,
                created_by=created_by,
                updated_by=updated_by,
                file_count=stats["file_count"],
                blank_lines=stats["blank_lines"],
                comment_lines=stats["comment_lines"],
                code_lines=stats["code_lines"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_created(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    owner_type: str = payload["installation"]["account"]["type"]
    owner_name: str = payload["installation"]["account"]["login"]
    owner_id: int = payload["installation"]["account"]["id"]
    repositories: list[dict[str, Any]] = payload["repositories"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)
    user_email: str | None = get_user_public_email(username=user_name, token=token)

    # Create installation record in Supabase
    create_installation(
        installation_id=installation_id,
        owner_type=owner_type,
        owner_name=owner_name,
        owner_id=owner_id,
        user_id=user_id,
        user_name=user_name,
        email=user_email,
    )

    # Process repositories
    process_repositories(
        owner_name=owner_name,
        owner_id=owner_id,
        repositories=repositories,
        token=token,
        created_by=user_name,
        updated_by=user_name,
    )


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    user_id: int = payload["sender"]["id"]
    delete_installation(installation_id=installation_id, user_id=user_id)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_repos_added(payload) -> None:
    installation_id: int = payload["installation"]["id"]
    sender_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get owner information
    owner_id = payload["installation"]["account"]["id"]
    owner_name = payload["installation"]["account"]["login"]

    # Process added repositories
    process_repositories(
        owner_name=owner_name,
        owner_id=owner_id,
        repositories=payload["repositories_added"],
        token=token,
        created_by=sender_name,
        updated_by=sender_name,
    )


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def handle_webhook_event(event_name: str, payload: dict[str, Any]) -> None:
    """
    Determine the event type and call the appropriate handler.
    Check the type of webhook event and handle accordingly.
    https://docs.github.com/en/apps/github-marketplace/using-the-github-marketplace-api-in-your-app/handling-new-purchases-and-free-trials
    https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=purchased#marketplace_purchase
    """
    action: str = payload.get("action")
    if not action:
        return

    # if event_name == "marketplace_purchase" and action in ("purchased"):
    #     print("Marketplace purchase is triggered")
    #     await handle_installation_created(payload=payload)

    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation
    if event_name == "installation" and action in ("created"):
        print("Installation is created")
        await handle_installation_created(payload=payload)
        return
    if event_name == "installation" and action in ("deleted"):
        print("Installation is deleted")
        await handle_installation_deleted(payload=payload)
        return

    # Add issue templates to the repositories when GitAuto is added to a repository
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories
    if event_name == "installation_repositories" and action in ("added"):
        await handle_installation_repos_added(payload=payload)
        return

    # Handle issue events
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issues
    if event_name == "issues":
        if action == "labeled":
            await handle_gitauto(
                payload=payload, trigger_type="label", input_from="github"
            )
            return
        if action == "opened":
            create_comment_on_issue_with_gitauto_button(payload=payload)
            return

    # Run GitAuto when checkbox is checked (edited)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    if event_name == "issue_comment" and action == "edited":
        search_text = "- [x] Generate PR"
        if PRODUCT_ID != "gitauto":
            search_text += " - " + PRODUCT_ID
            if payload["comment"]["body"].find(search_text) != -1:
                await handle_gitauto(
                    payload=payload, trigger_type="comment", input_from="github"
                )
        else:
            if (
                payload["comment"]["body"].find(search_text) != -1
                and payload["comment"]["body"].find(search_text + " - ") == -1
            ):
                await handle_gitauto(
                    payload=payload, trigger_type="comment", input_from="github"
                )
        return

    # Monitor check_run failure and re-run agent with failure reason
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#check_run
    if event_name == "check_run" and action in ("completed"):
        conclusion: str = payload["check_run"]["conclusion"]
        if conclusion in GITHUB_CHECK_RUN_FAILURES:
            # Cancel other in_progress check runs before handling this failure
            owner = payload["repository"]["owner"]["login"]
            repo = payload["repository"]["name"]
            commit_sha = payload["check_run"]["head_sha"]
            installation_id = payload["installation"]["id"]
            token = get_installation_access_token(installation_id=installation_id)

            cancel_workflow_runs_in_progress(
                owner=owner, repo=repo, commit_sha=commit_sha, token=token
            )

            handle_check_run(payload=payload)
        return

    # Write a PR description to the issue when GitAuto opened the PR
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "opened":
        write_pr_description(payload=payload)
        await handle_screenshot_comparison(payload=payload)
        return

    # Compare screenshots when the PR is synchronized
    if event_name == "pull_request" and action in ("synchronize"):
        await handle_screenshot_comparison(payload=payload)
        return

    # Track merged PRs as this is also our success status
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "closed":
        pull_request = payload.get("pull_request")
        if not pull_request:
            return

        # Check PR is merged and this is correct GitAuto environment
        merged_at = pull_request.get("merged_at", None)
        ref = pull_request.get("head", {}).get("ref", None)
        print(f"merged_at: {merged_at}")
        print(f"ref: {ref}")

        if (
            merged_at is not None
            and ref is not None
            and ref.startswith(PRODUCT_ID + ISSUE_NUMBER_FORMAT)
        ):
            # Get issue number from PR body
            body: str = pull_request["body"]
            if not body.startswith(PR_BODY_STARTS_WITH):
                print(f"PR body does not start with {PR_BODY_STARTS_WITH}")
                return

            issue_ref = body.split()[1]  # "Resolves #714" -> ["Resolves", "#714"]
            if not issue_ref.startswith("#"):
                print(f"Unexpected PR body format: {body}")
                return

            issue_number = int(issue_ref[1:])  # "#714" -> 714
            repository = payload["repository"]
            owner_type = repository["owner"]["type"]
            owner_name = repository["owner"]["login"]
            repo_name = repository["name"]
            set_issue_to_merged(
                owner_type=owner_type,
                owner_name=owner_name,
                repo_name=repo_name,
                issue_number=issue_number,
            )
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review_comment
    # Do nothing when action is "deleted"
    if event_name == "pull_request_review_comment" and action in ("created", "edited"):
        handle_review_run(payload=payload)
        return

    # Add workflow_run event handler
    if event_name == "workflow_run" and action == "completed":
        if payload["workflow_run"]["conclusion"] == "success":
            await handle_workflow_coverage(
                owner_id=payload["repository"]["owner"]["id"],
                owner_name=payload["repository"]["owner"]["login"],
                repo_id=payload["repository"]["id"],
                repo_name=payload["repository"]["name"],
                installation_id=payload["installation"]["id"],
                run_id=payload["workflow_run"]["id"],
                head_branch=payload["workflow_run"]["head_branch"],
                user_name=payload["sender"]["login"],
            )
        return

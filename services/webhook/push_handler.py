from services.git.get_clone_url import get_clone_url
from services.git.get_default_branch import get_default_branch
from services.github.branches.get_required_status_checks import (
    get_required_status_checks,
)
from services.github.pulls.get_open_pull_requests import get_open_pull_requests
from services.github.pulls.update_pull_request_branch import update_pull_request_branch
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.webhook.push import PushWebhookPayload
from services.supabase.repositories.get_repository import get_repository
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_push(payload: PushWebhookPayload):
    """https://docs.github.com/en/webhooks/webhook-events-and-payloads#push"""
    platform: Platform = "github"
    repository = payload["repository"]
    owner_id = repository["owner"]["id"]
    owner_name = repository["owner"]["login"]
    repo_id = repository["id"]
    repo_name = repository["name"]
    installation_id = payload["installation"]["id"]
    ref = payload["ref"]

    if not ref.startswith("refs/heads/"):
        logger.info(
            "Only process branch pushes (both local-to-remote and remote-to-remote) like refs/heads/main, ignore tag pushes like refs/tags/v1.0.0: %s",
            ref,
        )
        return None

    pushed_branch = ref.replace("refs/heads/", "")

    token = get_installation_access_token(installation_id=installation_id)

    # Fallback to default branch when target_branch is not configured (same as schedule_handler and handle_coverage_report)
    repo_settings = get_repository(
        platform=platform, owner_id=owner_id, repo_id=repo_id
    )
    target_branch = repo_settings.get("target_branch") if repo_settings else ""
    if target_branch:
        logger.info("Using custom target_branch: %s", target_branch)
    else:
        logger.info(
            "No custom target_branch configured, falling back to default branch"
        )
        clone_url = get_clone_url(owner=owner_name, repo=repo_name, token=token)
        target_branch = get_default_branch(clone_url=clone_url)
        if not target_branch:
            logger.info("Could not determine default branch")
            return None

    # Only update PRs when the configured target branch is pushed
    # NOT handled: local feature -> remote feature, remote feature -> remote staging
    # HANDLED: local main -> remote main, remote feature -> remote main (PR merge)
    if pushed_branch != target_branch:
        logger.info("Ignoring push to %s (target: %s)", pushed_branch, target_branch)
        return None

    # Check if this is a test-only push and the repo doesn't require up-to-date branches
    commits = payload.get("commits", [])
    if commits:
        logger.info("Inspecting %d commits for test-only push detection", len(commits))
        all_files: set[str] = set()
        for commit in commits:
            all_files.update(commit.get("added", []))
            all_files.update(commit.get("modified", []))
            all_files.update(commit.get("removed", []))
        if all_files and all(is_test_file(f) for f in all_files):
            logger.info(
                "Test-only push detected (%d files), checking branch protection",
                len(all_files),
            )
            protection = get_required_status_checks(
                owner=owner_name, repo=repo_name, branch=target_branch, token=token
            )
            if not protection.strict:
                logger.info(
                    "Skipping PR branch updates: test-only push to %s and strict=False",
                    target_branch,
                )
                return None

    open_prs = get_open_pull_requests(owner=owner_name, repo=repo_name, token=token)

    if not open_prs:
        logger.info("No open GitAuto PRs targeting %s", target_branch)
        return None

    updated_count = 0
    up_to_date_count = 0
    conflict_count = 0
    conflict_prs: list[int] = []
    failed_count = 0
    failures: list[str] = []
    for pr in open_prs:
        pr_number = pr["number"]
        status, error = update_pull_request_branch(
            owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
        )
        if status == "updated":
            logger.info("PR #%s branch updated", pr_number)
            updated_count += 1
        elif status == "up_to_date":
            logger.info("PR #%s branch already up-to-date", pr_number)
            up_to_date_count += 1
        elif status == "conflict":
            conflict_count += 1
            conflict_prs.append(pr_number)
            logger.warning(
                "PR #%s has merge conflicts with %s", pr_number, target_branch
            )
        else:
            failed_count += 1
            failures.append(f"PR #{pr_number}: {error}")
            logger.error("Failed to update PR #%s: %s", pr_number, error)

    result_msg = f"PR branch updates ({len(open_prs)} GitAuto PRs):\n- Updated: {updated_count}\n- Up-to-date: {up_to_date_count}\n- Conflicts: {conflict_count}\n- Failed: {failed_count}"
    if conflict_prs:
        logger.info("Appending conflict PR numbers to result message")
        result_msg += f"\nMerge conflicts: PR #{', #'.join(map(str, conflict_prs))}"
    if failures:
        logger.info("Appending failure messages to result message")
        result_msg += f"\nFailures: {', '.join(failures)}"
    logger.info(result_msg)

    return None

from typing import cast

from config import PRODUCT_ID
from constants.urls import DOC_URLS
from services.github.branches.get_required_status_checks import (
    get_required_status_checks,
)
from services.github.check_suites.get_check_suites import get_check_suites
from services.github.comments.create_comment import create_comment
from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.merge_pull_request import MergeMethod, merge_pull_request
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.check_suite import CheckSuite
from services.github.types.github_types import CheckSuiteCompletedPayload
from services.github.types.mergeable_state import MergeableState
from services.slack.slack_notify import slack_notify
from services.supabase.client import supabase
from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_config_file import is_config_file
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger, set_pr_number

BLOCKED = "Auto-merge blocked"

BLOCKED_STATE_REASONS: dict[MergeableState, str] = {
    "behind": "PR branch is behind base branch",
    "blocked": "The merge is blocked",
    "dirty": "merge conflicts detected",
    "draft": "PR is in draft mode",
    "unknown": "GitHub still calculating mergeability",
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_successful_check_suite(payload: CheckSuiteCompletedPayload):
    check_suite = payload["check_suite"]
    pull_requests = check_suite["pull_requests"]

    # Skip if no PR associated with this check run
    if not pull_requests:
        logger.info("No PRs associated with check_suite, skipping auto-merge")
        return

    pull_request = pull_requests[0]
    pr_number = pull_request["number"]
    pr_branch = pull_request["head"]["ref"]
    set_pr_number(pr_number)

    # Only auto-merge PRs created by GitAuto (check early to avoid unnecessary work)
    if not pr_branch.lower().startswith(f"{PRODUCT_ID.lower()}/"):
        logger.info("Not a GitAuto PR branch: %s, skipping auto-merge", pr_branch)
        return

    # Get repository info
    repo = payload["repository"]
    repo_id = repo["id"]
    owner_id = repo["owner"]["id"]
    owner_name = repo["owner"]["login"]
    repo_name = repo["name"]

    # Get installation token
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    # CRITICAL: Skip [skip ci] commits FIRST before any auto-merge logic.
    # When GitAuto creates a PR with an initial [skip ci] commit, GitHub fires
    # check_suite completed with conclusion=success (no checks ran = success).
    # Without this early check, the handler could attempt to auto-merge an empty PR.
    head_sha = check_suite["head_sha"]
    head_commit_message = check_suite["head_commit"]["message"]
    if "[skip ci]" in head_commit_message:
        logger.info("Last commit has [skip ci], skipping auto-merge check")
        return

    # Mark only the latest attempt as test-passed. A PR may have multiple usage
    # records (initial run failed → retry failed → final attempt succeeded).
    # The most recent record is the one whose code CI just validated.
    result = (
        supabase.table("usage")
        .select("id")
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .eq("owner_id", owner_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        logger.info("Marking usage record as test-passed")
        usage_id = result.data[0]["id"]
        (
            supabase.table("usage")
            .update({"is_test_passed": True})
            .eq("id", usage_id)
            .execute()
        )
    else:
        logger.info(
            "No usage record found for PR #%s, skipping test-passed update", pr_number
        )

    # Check if auto-merge is enabled BEFORE doing expensive API calls
    # (branch protection, check suites, PR details, etc.)
    repo_features = get_repository_features(owner_id=owner_id, repo_id=repo_id)
    if not repo_features or not repo_features.get("auto_merge"):
        logger.info("Skipping because auto-merge is disabled for repo_id=%s", repo_id)
        return

    comment_args = cast(
        BaseArgs,
        {
            "owner": owner_name,
            "repo": repo_name,
            "token": token,
            "pr_number": pr_number,
        },
    )

    base_branch = pull_request["base"]["ref"]

    all_suites = get_check_suites(
        owner=owner_name, repo=repo_name, ref=head_sha, token=token
    )
    if not all_suites:
        msg = f"Failed to fetch check suites for {head_sha}"
        logger.error(msg)
        raise RuntimeError(msg)

    protection = get_required_status_checks(
        owner=owner_name, repo=repo_name, branch=base_branch, token=token
    )

    # Filter out ghost suites: GitHub auto-creates a check suite for every installed app on each push, but apps that don't intend to run (e.g. GitAuto AI, Codecov) never create check runs, leaving the suite perpetually "queued". These would block auto-merge forever. A real suite (GitHub Actions, CircleCI) creates check runs immediately, even while queued.
    active_suites: list[CheckSuite] = []
    for suite in all_suites:
        app_name = suite["app"]["name"]
        if suite["status"] == "queued" and suite["latest_check_runs_count"] == 0:
            logger.info(
                "Skipping ghost suite '%s' because it is queued with 0 check runs",
                app_name,
            )
            continue

        logger.info(
            "Active suite '%s': status=%s, check_runs=%d",
            app_name,
            suite["status"],
            suite["latest_check_runs_count"],
        )
        active_suites.append(suite)

    if not active_suites:
        logger.info(
            "All %s suites are ghost suites, nothing to wait for", len(all_suites)
        )
        # Fall through to mergeable_state check below
    elif protection.checks:
        logger.info(
            "Using required status checks: %s (app_ids=%s)",
            protection.checks,
            protection.app_ids,
        )
        for suite in active_suites:
            app_name = suite["app"]["name"]
            app_id = suite["app"]["id"]
            status = suite["status"]
            if (
                protection.app_ids
                and app_id in protection.app_ids
                and status != "completed"
            ):
                logger.info(
                    "Returning because suite '%s' (app_id=%s) contains a required check and is not completed (status=%s)",
                    app_name,
                    app_id,
                    status,
                )
                return
        logger.info("All suites with required checks completed, proceeding to merge")
    else:
        if protection.checks is None:
            logger.info(
                "Could not read branch protection (status=%s), "
                "will return if any check suite is not completed",
                protection.status_code,
            )
        else:
            logger.info(
                "No required checks configured, "
                "will return if any check suite is not completed"
            )
        for suite in active_suites:
            app_name = suite["app"]["name"]
            status = suite["status"]
            if status != "completed":
                logger.info(
                    "Returning because check suite '%s' is not completed (status=%s)",
                    app_name,
                    status,
                )
                return

        logger.info(
            "All %s active check suites completed, proceeding to merge",
            len(active_suites),
        )

    # Fetch full PR details to get mergeable_state (not in simplified PR from check_suite webhook)
    full_pr = get_pull_request(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    if not full_pr:
        msg = f"Failed to fetch full PR details for #{pr_number}"
        logger.error(msg)
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)
        return

    mergeable_state = full_pr["mergeable_state"]
    logger.info("PR mergeable_state=%s", mergeable_state)

    # https://docs.github.com/en/graphql/reference/enums#mergestatestatus
    if mergeable_state in BLOCKED_STATE_REASONS:

        if mergeable_state == "blocked":
            logger.info(
                "Merge blocked because mergeable_state=blocked, checking active suite statuses"
            )
            check_statuses = [
                f"{s['app']['name']}: status={s['status']}, conclusion={s.get('conclusion', 'null')}"
                for s in active_suites
            ]
            reason = (
                BLOCKED_STATE_REASONS["blocked"]
                + ". Check suites: "
                + "; ".join(check_statuses)
            )
        else:
            logger.info("Merge blocked because mergeable_state=%s", mergeable_state)
            reason = BLOCKED_STATE_REASONS.get(mergeable_state, "unknown reason")

        # If any active check suite is still running, skip notification and return
        if any(s["status"] == "in_progress" for s in active_suites):
            logger.info("Returning because active check suites are still running")
            return

        msg = f"{BLOCKED}: mergeable_state={mergeable_state} ({reason})"
        logger.info(msg)

        # Delete any existing auto-merge blocked comments to avoid clutter
        delete_comments_by_identifiers(
            owner=owner_name,
            repo=repo_name,
            pr_number=pr_number,
            token=token,
            identifiers=[BLOCKED],
        )
        create_comment(body=msg, base_args=comment_args)
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)
        return

    logger.info(
        "PR mergeable_state=%s is acceptable, proceeding to merge", mergeable_state
    )

    # Get PR files
    changed_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )

    # Check if only test files restriction is enabled
    only_test_files = repo_features.get("auto_merge_only_test_files", False)
    if only_test_files:
        logger.info("auto_merge_only_test_files enabled, checking changed files")
        non_test_files = [
            f["filename"]
            for f in changed_files
            if not is_test_file(f["filename"]) and not is_config_file(f["filename"])
        ]
        if non_test_files:
            non_test_files_str = "\n".join(f"- `{f}`" for f in non_test_files)
            msg = f"{BLOCKED}: non-test files changed:\n{non_test_files_str}"
            logger.info(msg)

            delete_comments_by_identifiers(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                token=token,
                identifiers=[BLOCKED],
            )
            create_comment(body=msg, base_args=comment_args)
            slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
            slack_notify(slack_msg)
            return
        logger.info("All changed files are test/config files, proceeding to merge")
    else:
        logger.info("auto_merge_only_test_files disabled, skipping file check")

    # All conditions met - merge the PR
    merge_method = cast(MergeMethod, repo_features.get("merge_method", "merge"))
    msg = f"Auto-merging PR #{pr_number} with method={merge_method}"
    logger.info(msg)
    result = merge_pull_request(
        owner=owner_name,
        repo=repo_name,
        pr_number=pr_number,
        token=token,
        merge_method=merge_method,
    )

    if result and isinstance(result, dict) and result.get("code") == 405:
        msg = (
            f"{BLOCKED} by branch protection: {result.get('message')}\n\n"
            f"See {DOC_URLS['AUTO_MERGE']}"
        )
        logger.info(msg)
        delete_comments_by_identifiers(
            owner=owner_name,
            repo=repo_name,
            pr_number=pr_number,
            token=token,
            identifiers=[BLOCKED],
        )
        create_comment(body=msg, base_args=comment_args)
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)
        return

    logger.info("Auto-merge succeeded for PR #%s", pr_number)

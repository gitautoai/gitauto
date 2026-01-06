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
from services.github.commits.check_commit_has_skip_ci import check_commit_has_skip_ci
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.merge_pull_request import MergeMethod, merge_pull_request
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import BaseArgs, CheckSuiteCompletedPayload
from services.slack.slack_notify import slack_notify
from services.supabase.client import supabase
from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file

BLOCKED = "Auto-merge blocked"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_successful_check_suite(payload: CheckSuiteCompletedPayload):
    check_suite = payload["check_suite"]
    pull_requests = check_suite["pull_requests"]

    # Skip if no PR associated with this check run
    if not pull_requests:
        return

    pull_request = pull_requests[0]
    pr_number = pull_request["number"]
    pr_branch = pull_request["head"]["ref"]

    # Only auto-merge PRs created by GitAuto (check early to avoid unnecessary work)
    if not pr_branch.lower().startswith(f"{PRODUCT_ID.lower()}/"):
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

    head_sha = check_suite["head_sha"]
    base_branch = pull_request["base"]["ref"]

    all_suites = get_check_suites(
        owner=owner_name, repo=repo_name, ref=head_sha, token=token
    )
    if not all_suites:
        msg = f"Failed to fetch check suites for {owner_name}/{repo_name} PR #{pr_number}@{head_sha}"
        print(msg)
        raise RuntimeError(msg)

    # Create base_args for further API calls
    head_branch = check_suite["head_branch"]
    sender = payload["sender"]
    base_args: BaseArgs = {
        "input_from": "github",
        "owner_type": repo["owner"]["type"],
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": repo["clone_url"],
        "is_fork": repo.get("fork", False),
        "issue_number": pr_number,
        "issue_title": "",
        "issue_body": "",
        "issue_comments": [],
        "latest_commit_sha": head_sha,
        "issuer_name": sender["login"],
        "base_branch": head_branch,
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender["id"],
        "sender_name": sender["login"],
        "sender_email": f"{sender['login']}@users.noreply.github.com",
        "is_automation": True,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
    }

    _, required_checks = get_required_status_checks(
        owner=owner_name, repo=repo_name, branch=base_branch, token=token
    )

    if required_checks:
        print(f"Using required status checks: {required_checks}")
        for suite in all_suites:
            app_name = suite["app"]["name"]
            status = suite["status"]
            if app_name in required_checks and status != "completed":
                print(f"Required check '{app_name}' not completed: status={status}")
                return
        print("All required checks completed")
    else:
        print("No required checks configured, waiting for all check suites to complete")
        for suite in all_suites:
            app_name = suite["app"]["name"]
            status = suite["status"]
            if status != "completed":
                print(f"Check suite '{app_name}' not completed: status={status}")
                return

        print(f"All {len(all_suites)} check suites completed")

    # Get the most recent usage record for this PR
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

    # Update that record to mark test as passed
    if result.data:
        usage_id = result.data[0]["id"]
        (
            supabase.table("usage")
            .update({"is_test_passed": True})
            .eq("id", usage_id)
            .execute()
        )

    # Check if auto-merge should be performed
    repo_features = get_repository_features(owner_id=owner_id, repo_id=repo_id)
    if not repo_features or not repo_features.get("auto_merge"):
        msg = f"Auto-merge disabled for repo_id={repo_id}"
        print(msg)
        return

    # Check if last commit has [skip ci] - if so, tests never ran, trigger them
    if check_commit_has_skip_ci(
        owner=owner_name, repo=repo_name, commit_sha=head_sha, token=token
    ):
        msg = f"{BLOCKED}: last commit has [skip ci], triggering tests instead..."
        print(msg)

        delete_comments_by_identifiers(
            owner=owner_name,
            repo=repo_name,
            issue_number=pr_number,
            token=token,
            identifiers=[BLOCKED],
        )
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=pr_number,
            body=msg,
        )
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)

        create_empty_commit(
            base_args=base_args,
            message="Trigger tests",
        )
        return

    # Fetch full PR details to get mergeable_state (not in simplified PR from check_suite webhook)
    full_pr = get_pull_request(
        owner=owner_name, repo=repo_name, pull_number=pr_number, token=token
    )
    if not full_pr:
        msg = f"Failed to fetch full PR details for #{pr_number}"
        print(msg)
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)
        return

    # Check mergeable_state - only proceed if merging is allowed
    # https://docs.github.com/en/graphql/reference/enums#mergestatestatus
    mergeable_state = full_pr.get("mergeable_state", "")
    print(f"PR mergeable_state: {mergeable_state}")

    # Allow merge for: clean, unstable (failing non-required checks), has_hooks
    if mergeable_state not in ["clean", "unstable", "has_hooks"]:
        state_reasons = {
            "behind": "PR branch is behind base branch",
            "blocked": "The merge is blocked",
            "dirty": "merge conflicts detected",
            "draft": "PR is in draft mode",
            "unknown": "GitHub still calculating mergeability",
        }

        if mergeable_state == "blocked":
            check_statuses = [
                f"{s['app']['name']}: status={s['status']}, conclusion={s.get('conclusion', 'null')}"
                for s in all_suites
            ]
            reason = (
                state_reasons["blocked"]
                + ". Check suites: "
                + "; ".join(check_statuses)
            )
        else:
            reason = state_reasons.get(mergeable_state, "unknown reason")

        msg = f"{BLOCKED}: mergeable_state={mergeable_state} ({reason})"
        print(msg)

        # Delete any existing auto-merge blocked comments to avoid clutter
        delete_comments_by_identifiers(
            owner=owner_name,
            repo=repo_name,
            issue_number=pr_number,
            token=token,
            identifiers=[BLOCKED],
        )
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=pr_number,
            body=msg,
        )
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)
        return

    # Get PR files
    pull_url = pull_request["url"]
    pull_file_url = f"{pull_url}/files"
    changed_files = get_pull_request_files(url=pull_file_url, token=token)

    # Check if only test files restriction is enabled
    only_test_files = repo_features.get("auto_merge_only_test_files", False)
    if only_test_files:
        non_test_files = [
            f["filename"] for f in changed_files if not is_test_file(f["filename"])
        ]
        if non_test_files:
            non_test_files_str = "\n".join(f"- `{f}`" for f in non_test_files)
            msg = f"{BLOCKED}: non-test files changed:\n{non_test_files_str}"
            print(msg)

            delete_comments_by_identifiers(
                owner=owner_name,
                repo=repo_name,
                issue_number=pr_number,
                token=token,
                identifiers=[BLOCKED],
            )
            create_comment(
                owner=owner_name,
                repo=repo_name,
                token=token,
                issue_number=pr_number,
                body=msg,
            )
            slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
            slack_notify(slack_msg)
            return

    # All conditions met - merge the PR
    merge_method = cast(MergeMethod, repo_features.get("merge_method", "merge"))
    msg = f"Auto-merging PR #{pr_number} in {owner_name}/{repo_name} with method={merge_method}"
    print(msg)
    result = merge_pull_request(
        owner=owner_name,
        repo=repo_name,
        pull_number=pr_number,
        token=token,
        merge_method=merge_method,
    )

    if result and isinstance(result, dict) and result.get("code") == 405:
        msg = (
            f"{BLOCKED} by branch protection: {result.get('message')}\n\n"
            f"See {DOC_URLS['AUTO_MERGE']}"
        )
        print(msg)
        delete_comments_by_identifiers(
            owner=owner_name,
            repo=repo_name,
            issue_number=pr_number,
            token=token,
            identifiers=[BLOCKED],
        )
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=pr_number,
            body=msg,
        )
        slack_msg = f"`{owner_name}/{repo_name}` PR #{pr_number}: {msg}"
        slack_notify(slack_msg)

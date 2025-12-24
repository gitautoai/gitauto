from typing import cast

from services.github.comments.create_comment import create_comment
from services.github.commits.check_commit_has_skip_ci import check_commit_has_skip_ci
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.merge_pull_request import MergeMethod, merge_pull_request
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import BaseArgs, CheckSuiteCompletedPayload
from services.github.types.pull_request import PullRequest
from services.supabase.client import supabase
from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_successful_check_suite(payload: CheckSuiteCompletedPayload):
    check_suite = payload["check_suite"]
    pull_requests: list[PullRequest] = check_suite["pull_requests"]

    # Skip if no PR associated with this check run
    if not pull_requests:
        return

    pull_request = pull_requests[0]
    pr_number = pull_request["number"]

    # Get repository info
    repo = payload["repository"]
    repo_id = repo["id"]
    owner_id = repo["owner"]["id"]

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
    repo_features = get_repository_features(repo_id=repo_id)
    if not repo_features or not repo_features.get("auto_merge"):
        msg = f"Auto-merge disabled for repo_id={repo_id}"
        print(msg)
        return

    # Get installation token
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        msg = f"Failed to get installation token for installation_id={installation_id}"
        print(msg)
        return

    # Check if last commit has [skip ci] - if so, tests never ran, trigger them
    head_sha = check_suite["head_sha"]
    head_branch = check_suite["head_branch"]
    owner_name = repo["owner"]["login"]
    repo_name = repo["name"]
    if check_commit_has_skip_ci(
        owner=owner_name, repo=repo_name, commit_sha=head_sha, token=token
    ):
        msg = (
            "Auto-merge blocked: last commit has [skip ci], triggering tests instead..."
        )

        print(msg)
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=pr_number,
            body=msg,
        )

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

        create_empty_commit(
            base_args=base_args,
            message="Trigger tests",
        )
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
            msg = f"Auto-merge skipped: non-test files changed:\n{non_test_files_str}"
            print(msg)
            create_comment(
                owner=owner_name,
                repo=repo_name,
                token=token,
                issue_number=pr_number,
                body=msg,
            )
            return

    # Check mergeable_state
    mergeable_state = pull_request.get("mergeable_state", "")
    if mergeable_state != "clean":
        state_reasons = {
            "blocked": "required checks or approvals missing",
            "behind": "PR branch is behind base branch",
            "dirty": "merge conflicts detected",
            "unstable": "some checks failing",
            "unknown": "GitHub still calculating mergeability",
        }
        reason = state_reasons.get(mergeable_state, "unknown reason")
        msg = f"Auto-merge blocked: mergeable_state={mergeable_state} ({reason})"
        print(msg)
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=pr_number,
            body=msg,
        )
        return

    # All conditions met - merge the PR
    merge_method = cast(MergeMethod, repo_features.get("merge_method", "merge"))
    msg = f"Auto-merging PR #{pr_number} in {owner_name}/{repo_name} with method={merge_method}"
    print(msg)
    merge_pull_request(
        owner=owner_name,
        repo=repo_name,
        pull_number=pr_number,
        token=token,
        merge_method=merge_method,
    )

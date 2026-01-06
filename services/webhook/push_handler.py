import logging
from services.github.pulls.get_open_pull_requests import get_open_pull_requests
from services.github.pulls.update_pull_request_branch import update_pull_request_branch
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.webhook.push import PushWebhookPayload
from services.slack.slack_notify import slack_notify
from services.supabase.repositories.get_repository import get_repository
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def handle_push(payload: PushWebhookPayload):
    """https://docs.github.com/en/webhooks/webhook-events-and-payloads#push"""
    repository = payload["repository"]
    owner_id = repository["owner"]["id"]
    owner_name = repository["owner"]["login"]
    repo_id = repository["id"]
    repo_name = repository["name"]
    installation_id = payload["installation"]["id"]
    ref = payload["ref"]

    if not ref.startswith("refs/heads/"):
        # Only process branch pushes (both local-to-remote and remote-to-remote) like refs/heads/main, ignore tag pushes like refs/tags/v1.0.0
        return None

    pushed_branch = ref.replace("refs/heads/", "")

    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings:
        # Repository settings not found in database
        return None

    target_branch = repo_settings.get("target_branch")
    if not target_branch or pushed_branch != target_branch:
        # Only update PRs when the configured target branch is pushed
        # NOT handled: local feature -> remote feature, remote feature -> remote staging
        # HANDLED: local main -> remote main, remote feature -> remote main (PR merge)
        return None

    token = get_installation_access_token(installation_id=installation_id)

    open_prs = get_open_pull_requests(
        owner=owner_name, repo=repo_name, target_branch=target_branch, token=token
    )

    if not open_prs:
        # No GitAuto PRs targeting this branch
        return None

    updated_count = 0
    up_to_date_count = 0
    failed_count = 0
    failures = []
    for pr in open_prs:
        pr_number = pr["number"]
        status, error = update_pull_request_branch(
            owner=owner_name, repo=repo_name, pull_number=pr_number, token=token
        )
        if status == "updated":
            updated_count += 1
        elif status == "up_to_date":
            up_to_date_count += 1
        else:
            failed_count += 1
            failures.append(f"PR #{pr_number}: {error}")
            logging.warning(
                "Failed to update PR #%s in %s/%s: %s",
                pr_number,
                owner_name,
                repo_name,
                error,
            )

    result_msg = f"Updated {updated_count}, already up-to-date {up_to_date_count}, failed {failed_count} out of {len(open_prs)} GitAuto PR(s) in `{owner_name}/{repo_name}`"
    if failures:
        result_msg += f"\nFailures: {', '.join(failures)}"
    slack_notify(result_msg)

    return None

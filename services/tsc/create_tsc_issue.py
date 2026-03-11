from services.github.issues.create_issue import create_issue
from services.github.issues.issue_exists import issue_exists
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

TSC_ISSUE_TITLE = "Fix pre-existing TypeScript type errors"
MAX_ERRORS_IN_BODY = 50


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_tsc_issue(
    *,
    base_args: BaseArgs,
    unrelated_errors: list[str],
):
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    token = base_args.get("token", "")

    if issue_exists(owner=owner, repo=repo, token=token, title=TSC_ISSUE_TITLE):
        logger.info("tsc: Issue for pre-existing errors already exists, skipping")
        return

    error_list = "\n".join(f"- `{e}`" for e in unrelated_errors[:MAX_ERRORS_IN_BODY])
    body = (
        "## Pre-existing TypeScript type errors\n\n"
        "These errors were detected by `tsc --noEmit` and exist independently of any "
        "recent PR changes. They should be fixed to keep the codebase clean.\n\n"
        f"### Errors ({len(unrelated_errors)} total)\n\n"
        f"{error_list}\n"
    )
    if len(unrelated_errors) > MAX_ERRORS_IN_BODY:
        body += f"\n... and {len(unrelated_errors) - MAX_ERRORS_IN_BODY} more errors.\n"

    status_code, issue = create_issue(
        owner=owner,
        repo=repo,
        token=token,
        title=TSC_ISSUE_TITLE,
        body=body,
        assignees=[base_args.get("sender_name", "")],
        labels=[],
    )

    if status_code == 200 and issue:
        logger.info(
            "tsc: Created issue for pre-existing errors: %s", issue.get("html_url")
        )
    elif status_code == 410:
        logger.info("tsc: Issues disabled for repo, skipping")

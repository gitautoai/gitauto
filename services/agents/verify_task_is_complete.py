# Local imports
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value={"success": True, "message": "Task completed."},
    raise_on_error=False,
)
def verify_task_is_complete(base_args: BaseArgs, **_kwargs):
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    pull_number = base_args.get("pull_number")
    token = base_args.get("token", "")

    if not pull_number:
        raise ValueError("pull_number is required for verify_task_is_complete")

    pr_files = get_pull_request_files(
        owner=owner, repo=repo, pull_number=pull_number, token=token
    )

    if pr_files:
        return {
            "success": True,
            "message": "Task completed successfully. PR has changes.",
        }

    return {
        "success": False,
        "message": "Error: Cannot complete task - the PR has no changes. You must make actual code changes before calling verify_task_is_complete. Use apply_diff_to_file or replace_remote_file_content to commit your changes first.",
    }

from anthropic.types import ToolUnionParam

from services.git.git_commit_and_push import git_commit_and_push
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset
from services.git.reapply_files import reapply_files
from services.git.save_pr_files import save_pr_files
from services.github.pulls.change_pr_base_branch import change_pr_base_branch
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.pull_request_file import Status
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

RESET_PR_BRANCH_TO_NEW_BASE: ToolUnionParam = {
    "name": "reset_pr_branch_to_new_base",
    "description": "Changes the base branch of the current pull request and resets the PR branch onto the new base. Use this when a reviewer requests the PR to target a different branch (e.g., from 'release/20260408' to 'release/20260422').",
    "input_schema": {
        "type": "object",
        "properties": {
            "new_base_branch": {
                "type": "string",
                "description": "The name of the new base branch to target (e.g., 'release/20260422').",
            },
        },
        "required": ["new_base_branch"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def reset_pr_branch_to_new_base(base_args: BaseArgs, new_base_branch: str, **_kwargs):
    """Save PR file changes, change the base branch, reset to the new base, and rewrite files.
    This avoids a diverged diff when the old and new base branches are siblings (e.g. release/20260408 → release/20260422).
    """
    owner = base_args["owner"]
    repo = base_args["repo"]
    pr_number = base_args["pr_number"]
    token = base_args["token"]
    clone_dir = base_args["clone_dir"]
    clone_url = base_args["clone_url"]

    # 1. Get the list of files changed in this PR
    logger.info("Getting PR files for %s/%s#%d", owner, repo, pr_number)
    pr_files = get_pull_request_files(
        owner=owner, repo=repo, pr_number=pr_number, token=token
    )
    if not pr_files:
        logger.warning("No PR files found, only changing base branch")

    # 2. Save file contents from the current branch before reset
    logger.info("Saving %d PR file contents before reset", len(pr_files))
    saved_files, deleted_files = save_pr_files(clone_dir=clone_dir, pr_files=pr_files)

    # 3. Change the base branch on GitHub (metadata only)
    logger.info("Changing base branch to %s on GitHub", new_base_branch)
    result = change_pr_base_branch(base_args=base_args, new_base_branch=new_base_branch)
    if not result:
        logger.error("Failed to change base branch to %s", new_base_branch)
        return None

    # 4. Reset local branch to the new base
    logger.info("Fetching and resetting to %s", new_base_branch)
    git_fetch(target_dir=clone_dir, clone_url=clone_url, branch=new_base_branch)
    git_reset(target_dir=clone_dir)

    # 5. Rewrite saved files onto the new base
    logger.info("Reapplying files onto new base")
    files_to_commit = reapply_files(
        clone_dir=clone_dir, saved_files=saved_files, deleted_files=deleted_files
    )
    if not files_to_commit:
        logger.info("No files to rewrite after reset")
        return result

    # 6. Commit per file and force push (first push forces because local history diverged from remote after reset)
    base_args["base_branch"] = new_base_branch
    status_map: dict[str, Status] = {f["filename"]: f["status"] for f in pr_files}
    for i, file_path in enumerate(files_to_commit):
        status = status_map[file_path]
        if status == "removed":
            verb = "Delete"
        elif status == "added":
            verb = "Add"
        else:
            verb = "Update"
        logger.info(
            "Committing %d/%d: %s %s", i + 1, len(files_to_commit), verb, file_path
        )
        git_commit_and_push(
            base_args=base_args,
            message=f"{verb} {file_path}",
            files=[file_path],
            force=i == 0,
        )

    logger.info("Reset %d files onto %s", len(files_to_commit), new_base_branch)
    return f"{result}. Reset {len(files_to_commit)} files onto {new_base_branch}."

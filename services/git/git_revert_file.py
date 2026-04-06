# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.claude.tools.file_modify_result import FileWriteResult
from services.claude.tools.properties import FILE_PATH
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

GIT_REVERT_FILE: ToolUnionParam = {
    "name": "git_revert_file",
    "description": "Reverts a single file to its state before the agent started making changes. Use this when you've gotten lost or your changes to a file are too broken to fix - this lets you start over for that file. Only affects the specified file - other files are untouched.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": FILE_PATH,
        },
        "required": ["file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value=lambda file_path, base_args, **_kwargs: FileWriteResult(
        success=False,
        message="git_revert_file failed.",
        file_path=file_path,
        content=read_local_file(file_path, base_args["clone_dir"]) or "",
    ),
    raise_on_error=False,
)
def git_revert_file(file_path: str, base_args: BaseArgs, **_kwargs):
    clone_dir = base_args["clone_dir"]
    # Use the commit SHA from before the agent started (check_suite/review handlers),
    # falling back to base_branch for new_pr_handler where no prior commits exist
    latest_sha = base_args.get("latest_commit_sha")
    base_branch = base_args["base_branch"]
    revert_ref = latest_sha or base_branch

    run_subprocess(["git", "checkout", revert_ref, "--", file_path], clone_dir)
    logger.info("git_revert_file: reverted %s to %s", file_path, revert_ref)

    if latest_sha:
        description = (
            f"{file_path} to the version before agent started ({latest_sha[:7]})"
        )
    else:
        description = f"{file_path} to {base_branch}"
    git_commit_and_push(
        base_args=base_args,
        message=f"Revert {description}",
        files=[file_path],
    )

    content = read_local_file(file_path, clone_dir) or ""
    return FileWriteResult(
        success=True,
        message=f"Reverted {description}",
        file_path=file_path,
        content=content,
    )

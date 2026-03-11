# Standard imports
import os
import shutil

# Local imports
from services.claude.tools.file_modify_result import FileMoveResult
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(
    default_return_value=lambda old_file_path, new_file_path, base_args, **kwargs: FileMoveResult(
        success=False,
        message="Unexpected error occurred.",
        old_file_path=old_file_path,
        new_file_path=new_file_path,
    ),
    raise_on_error=False,
)
def move_file(
    old_file_path: str,
    new_file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Move a file in the local clone, then commit and push to the PR branch."""
    if old_file_path == new_file_path:
        return FileMoveResult(
            success=False,
            message=f"Source and destination cannot be the same: '{old_file_path}'.",
            old_file_path=old_file_path,
            new_file_path=new_file_path,
        )

    clone_dir = base_args["clone_dir"]
    old_local_path = os.path.join(clone_dir, old_file_path)
    new_local_path = os.path.join(clone_dir, new_file_path)

    # Check source file exists
    if not os.path.exists(old_local_path):
        return FileMoveResult(
            success=False,
            message=f"File '{old_file_path}' not found.",
            old_file_path=old_file_path,
            new_file_path=new_file_path,
        )

    # Check target doesn't already exist
    if os.path.exists(new_local_path):
        return FileMoveResult(
            success=False,
            message=f"Target file '{new_file_path}' already exists.",
            old_file_path=old_file_path,
            new_file_path=new_file_path,
        )

    # Move the file locally
    os.makedirs(os.path.dirname(new_local_path), exist_ok=True)
    shutil.move(old_local_path, new_local_path)
    logger.info("Moved local: %s -> %s", old_local_path, new_local_path)

    # Stage both old (deleted) and new (added) paths
    git_commit_and_push(
        base_args=base_args,
        message=f"Move {old_file_path} to {new_file_path}",
        files=[old_file_path, new_file_path],
    )

    return FileMoveResult(
        success=True,
        message=f"Moved {old_file_path} to {new_file_path}.",
        old_file_path=old_file_path,
        new_file_path=new_file_path,
    )

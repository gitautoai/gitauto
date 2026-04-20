# Standard imports
import os
import shutil

# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.claude.tools.file_modify_result import FileMoveResult
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
MOVE_FILE: ToolUnionParam = {
    "name": "move_file",
    "description": "Moves a file to a new location in the GitHub repository. This is useful for resolving naming conflicts, improving code organization, or fixing pytest import collisions caused by duplicate filenames.",
    "input_schema": {
        "type": "object",
        "properties": {
            "old_file_path": {
                "type": "string",
                "description": "The current path of the file to be moved. For example, 'src/old_name.py'.",
            },
            "new_file_path": {
                "type": "string",
                "description": "The new path for the file. For example, 'src/new_name.py'. Must be different from old_file_path.",
            },
        },
        "required": ["old_file_path", "new_file_path"],
        "additionalProperties": False,
    },
    "strict": True,
}


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
        logger.warning(
            "move_file: refusing no-op move (old and new path are both %s)",
            old_file_path,
        )
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
        logger.warning(
            "move_file: source %s not found in clone_dir; aborting", old_file_path
        )
        return FileMoveResult(
            success=False,
            message=f"File '{old_file_path}' not found.",
            old_file_path=old_file_path,
            new_file_path=new_file_path,
        )

    # Check target doesn't already exist
    if os.path.exists(new_local_path):
        logger.warning(
            "move_file: target %s already exists; refusing to overwrite", new_file_path
        )
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
    commit_result = git_commit_and_push(
        base_args=base_args,
        message=f"Move {old_file_path} to {new_file_path}",
        files=[old_file_path, new_file_path],
    )
    if not commit_result.success:
        logger.warning(
            "move_file: push for %s->%s failed (concurrent_push_detected=%s on %s)",
            old_file_path,
            new_file_path,
            commit_result.concurrent_push_detected,
            base_args["new_branch"],
        )
        return FileMoveResult(
            success=False,
            message=(
                f"Concurrent push detected on `{base_args['new_branch']}` while moving {old_file_path} to {new_file_path}. Another commit landed; aborting."
                if commit_result.concurrent_push_detected
                else f"Failed to commit/push move of {old_file_path} to {new_file_path}."
            ),
            old_file_path=old_file_path,
            new_file_path=new_file_path,
            concurrent_push_detected=commit_result.concurrent_push_detected,
        )

    logger.info(
        "move_file: %s -> %s committed and pushed", old_file_path, new_file_path
    )
    return FileMoveResult(
        success=True,
        message=f"Moved {old_file_path} to {new_file_path}.",
        old_file_path=old_file_path,
        new_file_path=new_file_path,
    )

# Standard imports
import os

# Third party imports
from anthropic.types import ToolUnionParam

# Local imports
from config import UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.claude.tools.properties import FILE_PATH
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.apply_patch import apply_patch
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger
from utils.prompts.diff import DIFF_DESCRIPTION

DIFF: dict[str, str] = {
    "type": "string",
    "description": DIFF_DESCRIPTION,
}

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
APPLY_DIFF_TO_FILE: ToolUnionParam = {
    "name": "apply_diff_to_file",
    "description": "Applies a diff to an EXISTING file in the local clone and commits the change to the PR branch. Do NOT use this to create new files - use replace_remote_file_content instead. For targeted edits, prefer search_and_replace which uses content matching instead of line numbers.",
    "input_schema": {
        "type": "object",
        "properties": {"file_path": FILE_PATH, "diff": DIFF},
        "required": ["file_path", "diff"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(
    default_return_value=lambda diff, file_path, base_args, **kwargs: FileWriteResult(
        success=False,
        message="Unexpected error occurred.",
        file_path=file_path,
        content="",
    ),
    raise_on_error=False,
)
def apply_diff_to_file(
    diff: str,
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Apply a unified diff to a file in the local clone, then commit and push to the PR branch."""
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)

    # Check if path is a directory
    if os.path.isdir(local_path):
        logger.warning(
            "apply_diff_to_file: %s is a directory, not a file; aborting", file_path
        )
        return FileWriteResult(
            success=False,
            message=f"'{file_path}' is a directory, not a file.",
            file_path=file_path,
            content="",
        )

    original_text = read_local_file(file_path, clone_dir)
    file_exists = original_text is not None
    if not original_text:
        logger.info(
            "apply_diff_to_file: %s has no existing content; treating as new file",
            file_path,
        )
        original_text = ""

    # Apply the diff locally
    result = apply_patch(
        original_text=original_text,
        diff_text=diff,
        clone_dir=clone_dir,
        file_path=file_path,
    )

    if result.error:
        logger.warning(
            "apply_diff_to_file: apply_patch returned error for %s: %s",
            file_path,
            result.error,
        )
        return FileWriteResult(
            success=False,
            message=result.error,
            file_path=file_path,
            content=original_text,
        )

    # Handle file deletion
    if result.content == "" and "+++ /dev/null" in diff:
        logger.info(
            "apply_diff_to_file: diff is a deletion for %s; removing local file",
            file_path,
        )
        if os.path.exists(local_path):
            logger.info(
                "apply_diff_to_file: %s exists on disk; calling os.remove", local_path
            )
            os.remove(local_path)
            logger.info("Deleted local: %s", local_path)
        del_result = git_commit_and_push(
            base_args=base_args, message=f"Delete {file_path}", files=[file_path]
        )
        if not del_result.success:
            logger.warning(
                "apply_diff_to_file: delete-commit for %s failed (concurrent_push_detected=%s on %s)",
                file_path,
                del_result.concurrent_push_detected,
                base_args["new_branch"],
            )
            return FileWriteResult(
                success=False,
                message=(
                    f"Concurrent push detected on `{base_args['new_branch']}` while deleting {file_path}. Another commit landed; aborting."
                    if del_result.concurrent_push_detected
                    else f"Failed to commit deletion of {file_path}."
                ),
                file_path=file_path,
                content="",
                concurrent_push_detected=del_result.concurrent_push_detected,
            )

        logger.info("apply_diff_to_file: %s deletion committed and pushed", file_path)
        return FileWriteResult(
            success=True,
            message=f"Deleted {file_path}.",
            file_path=file_path,
            content="",
        )

    # Skip if content is identical
    if result.content == original_text:
        logger.info("No changes to %s, skipping", file_path)
        return FileWriteResult(
            success=False,
            message=f"No changes to {file_path}.",
            file_path=file_path,
            content=result.content,
        )

    # Write the patched content to the local clone
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding=UTF8) as f:
        f.write(result.content)
    logger.info("%s: %s", "Updated" if file_exists else "Created", local_path)

    commit_result = git_commit_and_push(
        base_args=base_args,
        message=f"{'Update' if file_exists else 'Create'} {file_path}",
        files=[file_path],
    )
    if not commit_result.success:
        logger.warning(
            "apply_diff_to_file: push for %s failed (concurrent_push_detected=%s on %s)",
            file_path,
            commit_result.concurrent_push_detected,
            base_args["new_branch"],
        )
        return FileWriteResult(
            success=False,
            message=(
                f"Concurrent push detected on `{base_args['new_branch']}` while committing {file_path}. Another commit landed; aborting this edit."
                if commit_result.concurrent_push_detected
                else f"Failed to commit/push {file_path}."
            ),
            file_path=file_path,
            content="",
            concurrent_push_detected=commit_result.concurrent_push_detected,
        )

    logger.info("apply_diff_to_file: %s patch committed and pushed", file_path)
    return FileWriteResult(
        success=True,
        message=f"{'Updated' if file_exists else 'Created'} {file_path}.",
        file_path=file_path,
        content=result.content,
    )

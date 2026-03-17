# Standard imports
import os

# Local imports
from config import UTF8
from services.claude.tools.file_modify_result import FileWriteResult
from services.git.git_commit_and_push import git_commit_and_push
from services.git.git_show_head_file import git_show_head_file
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.apply_patch import apply_patch
from utils.logging.logging_config import logger


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
        return FileWriteResult(
            success=False,
            message=f"'{file_path}' is a directory, not a file.",
            file_path=file_path,
            content="",
        )

    # Compare against last committed version (not disk, which formatters may have modified)
    original_text = git_show_head_file(file_path=file_path, clone_dir=clone_dir)
    file_exists = original_text is not None
    if not original_text:
        original_text = ""

    # Apply the diff locally
    result = apply_patch(
        original_text=original_text,
        diff_text=diff,
        clone_dir=clone_dir,
        file_path=file_path,
    )

    if result.error:
        return FileWriteResult(
            success=False,
            message=result.error,
            file_path=file_path,
            content=original_text,
        )

    # Handle file deletion
    if result.content == "" and "+++ /dev/null" in diff:
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info("Deleted local: %s", local_path)
        git_commit_and_push(
            base_args=base_args, message=f"Delete {file_path}", files=[file_path]
        )
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

    git_commit_and_push(
        base_args=base_args,
        message=f"{'Update' if file_exists else 'Create'} {file_path}",
        files=[file_path],
    )

    return FileWriteResult(
        success=True,
        message=f"{'Updated' if file_exists else 'Created'} {file_path}.",
        file_path=file_path,
        content=result.content,
    )

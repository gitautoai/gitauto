# Standard imports
import os

# Local imports
from services.git.git_commit_and_push import git_commit_and_push
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_file(
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Delete a file from the local clone, then commit and push to the PR branch."""
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)

    if os.path.isdir(local_path):
        return f"Error: '{file_path}' is a directory, not a file"

    if not os.path.exists(local_path):
        return f"Error: File {file_path} not found"

    os.remove(local_path)
    logger.info("Deleted local: %s", local_path)

    git_commit_and_push(
        base_args=base_args, message=f"Delete {file_path}", files=[file_path]
    )

    return f"File {file_path} successfully deleted"

# Standard imports
import os

# Local imports
from services.github.files.delete_remote_file import delete_remote_file
from services.github.files.get_file_info import get_file_info
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_file(
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Delete a file from the GitHub repository and locally."""
    # Get file info including SHA
    file_info = get_file_info(file_path, base_args)

    if file_info is None:
        return f"Error: File {file_path} not found or is a directory"

    sha = file_info.get("sha")
    if not sha or not sha.strip():
        return f"Error: Unable to get SHA for file {file_path}"

    # Delete the file on GitHub
    result = delete_remote_file(file_path, sha, base_args)

    # Delete the local file for verification (tsc, jest, eslint, etc.)
    clone_dir = base_args["clone_dir"]
    local_path = os.path.join(clone_dir, file_path)
    if os.path.exists(local_path):
        os.remove(local_path)
        logger.info("Deleted local: %s", local_path)

    return result

# Local imports
from services.github.files.delete_file_by_sha import delete_file_by_sha
from services.github.files.get_file_info import get_file_info
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_file(
    file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Delete a file from the GitHub repository."""
    # Get file info including SHA
    file_info = get_file_info(file_path, base_args)

    if file_info is None:
        return f"Error: File {file_path} not found or is a directory"

    sha = file_info.get("sha")
    if not sha:
        return f"Error: Unable to get SHA for file {file_path}"

    # Delete the file using the SHA
    return delete_file_by_sha(file_path, sha, base_args)

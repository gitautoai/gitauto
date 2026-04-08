from typing import Sequence

from services.github.pulls.get_pull_request_files import FileChange
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=({}, []), raise_on_error=False)
def save_pr_files(clone_dir: str, pr_files: Sequence[FileChange]):
    """Read PR file contents from clone_dir before a destructive operation like rebase.
    Returns (saved_files dict, deleted_files list) where saved_files maps file_path -> content.
    """
    saved_files: dict[str, str] = {}
    deleted_files: list[str] = []
    for file_change in pr_files:
        file_path = file_change["filename"]
        if file_change["status"] == "removed":
            deleted_files.append(file_path)
            logger.info("Will delete after rebase: %s", file_path)
            continue

        content = read_local_file(file_path=file_path, base_dir=clone_dir)
        if content is None:
            logger.warning("Could not read file, skipping: %s", file_path)
            continue
        saved_files[file_path] = content

    logger.info(
        "Saved %d files and %d deletions from PR",
        len(saved_files),
        len(deleted_files),
    )
    return (saved_files, deleted_files)

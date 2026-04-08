import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def reapply_files(
    clone_dir: str,
    saved_files: dict[str, str],
    deleted_files: list[str],
):
    """Write saved file contents back to clone_dir after a rebase.
    Returns list of file paths that were modified (for staging/committing).
    """
    files_to_commit: list[str] = []
    for file_path, content in saved_files.items():
        full_path = os.path.join(clone_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding=UTF8, newline="") as f:
            f.write(content)
        logger.info("Wrote file: %s", file_path)
        files_to_commit.append(file_path)

    for file_path in deleted_files:
        full_path = os.path.join(clone_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info("Deleted file: %s", file_path)
            files_to_commit.append(file_path)
        else:
            logger.warning("File to delete not found, skipping: %s", file_path)

    logger.info("Reapplied %d files after rebase", len(files_to_commit))
    return files_to_commit

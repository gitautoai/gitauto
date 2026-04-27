import os

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def list_local_directory(dir_path: str):
    """Return entries in `dir_path`, sorted as `dirs/ first, then files`, each on a single string. Mirrors `ls` output.

    Directories carry a trailing slash so callers (and the LLM) can tell them apart from files at a glance. Returns [] when dir_path is missing or not a directory — same swallow-and-default contract used everywhere else in utils/files.

    Used by get_local_file_tree (the agent's directory-listing tool) and by read_local_file (when the agent passes a directory path; we hand back a listing instead of crashing on open()).
    """
    if not os.path.isdir(dir_path):
        logger.info("list_local_directory: %s is not a directory", dir_path)
        return []

    entries = os.listdir(dir_path)
    dirs: list[str] = []
    files: list[str] = []

    for entry in entries:
        full_path = os.path.join(dir_path, entry)
        if os.path.isdir(full_path):
            logger.debug("list_local_directory: dir entry %s", entry)
            dirs.append(f"{entry}/")
        else:
            logger.debug("list_local_directory: file entry %s", entry)
            files.append(entry)

    result = sorted(dirs) + sorted(files)
    logger.info(
        "list_local_directory: %s -> %d dirs + %d files",
        dir_path,
        len(dirs),
        len(files),
    )
    return result

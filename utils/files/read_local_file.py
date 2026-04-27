import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.files.list_local_directory import list_local_directory
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def read_local_file(file_path: str, base_dir: str):
    """Read a file from the local filesystem."""
    full_path = os.path.join(base_dir, file_path)
    if not os.path.exists(full_path):
        logger.warning("File not found: %s", full_path)
        return None

    # When the path is a directory, return a listing instead of crashing on open().
    # Sentry AGENT-3KP/3KN: agent passed src/auth/__mocks__ as a file path; old code fell through os.path.exists and raised IsADirectoryError on open().
    # Listing back lets the agent see what's actually there and pick a real file in a follow-up call, no extra get_local_file_tree round trip.
    if os.path.isdir(full_path):
        entries = list_local_directory(full_path)
        listing = "\n".join(entries)
        logger.warning(
            "read_local_file: %s is a directory; returning %d-entry listing instead",
            full_path,
            len(entries),
        )
        return f"# `{file_path}` is a directory. Contents:\n{listing}"

    # Non-regular but non-directory paths (broken symlinks, FIFOs, sockets) — open() would raise. Treat as missing.
    if not os.path.isfile(full_path):
        logger.warning(
            "read_local_file: %s is a non-regular file; treating as missing", full_path
        )
        return None

    # newline="" preserves original line endings (\r\n) instead of Python's default normalization to \n.
    # errors="replace" substitutes U+FFFD for malformed bytes instead of raising UnicodeDecodeError.
    with open(full_path, "r", encoding=UTF8, newline="", errors="replace") as f:
        content = f.read()
        logger.info(
            "read_local_file: returning %d chars from %s", len(content), full_path
        )
        return content

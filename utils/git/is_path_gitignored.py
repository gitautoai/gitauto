import subprocess

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_path_gitignored(clone_dir: str, file_path: str):
    """Return True when `file_path` (relative to clone_dir) would be ignored by git.

    Uses `git check-ignore -q`. Exit 0 means ignored; exit 1 means not ignored;
    anything else is a real error. We bypass run_subprocess() because it raises on
    any non-zero exit, which would hide the legitimate exit-1 "not ignored" signal
    behind a ValueError."""
    logger.info("is_path_gitignored: checking %s", file_path)
    result = subprocess.run(
        ["git", "check-ignore", "-q", file_path],
        capture_output=True,
        check=False,
        cwd=clone_dir,
        text=True,
        shell=False,
    )
    ignored = result.returncode == 0
    logger.info(
        "is_path_gitignored: %s -> ignored=%s (exit=%d)",
        file_path,
        ignored,
        result.returncode,
    )
    return ignored

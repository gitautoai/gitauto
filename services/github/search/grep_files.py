import os
import subprocess

from services.github.search.grep_patterns import GREP_EXCLUDE_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def grep_files(query: str, search_dir: str):
    """Run grep -r -l on search_dir and return matching file paths."""
    if not os.path.isdir(search_dir):
        logger.warning("Directory not found: %s", search_dir)
        return list[str]()

    result = subprocess.run(
        [
            "grep",
            "-r",  # Recursive search
            "-l",  # Filenames only, not matching lines
            # Skip binary files (images, compiled files, etc.)
            "--binary-files=without-match",
            *GREP_EXCLUDE_DIRS,
            "-e",
            query,  # -e explicitly marks the search pattern
            ".",  # Search under search_dir (set via cwd)
        ],
        capture_output=True,
        check=False,
        cwd=search_dir,
        text=True,
        timeout=30,
    )

    # grep returns 1 when no matches found (not an error)
    if result.returncode not in (0, 1):
        logger.warning(
            "grep failed with return code %d: %s", result.returncode, result.stderr
        )
        return list[str]()

    if not result.stdout.strip():
        return list[str]()

    # grep outputs relative paths (e.g. ./src/main.py) since we use cwd=search_dir
    return [
        line.strip().removeprefix("./") for line in result.stdout.strip().split("\n")
    ]

import os
import subprocess

from utils.files.grep_patterns import GREP_EXCLUDE_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value={}, raise_on_error=False)
def grep_files(query: str, search_dir: str):
    """Run grep -r -n on search_dir and return matching file paths with lines."""
    if not os.path.isdir(search_dir):
        logger.warning("Directory not found: %s", search_dir)
        return dict[str, list[str]]()

    result = subprocess.run(
        [
            "grep",
            "-r",  # Recursive search
            "-n",  # Show line numbers with matching lines
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
        return dict[str, list[str]]()

    if not result.stdout.strip():
        return dict[str, list[str]]()

    # Parse grep -n output: ./path/to/file:123:matching line content
    matches: dict[str, list[str]] = {}
    for line in result.stdout.strip().split("\n"):
        # Split on first two colons: file_path:line_number:content
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        file_path = parts[0].strip().removeprefix("./")
        line_num = parts[1]
        content = parts[2]
        if file_path not in matches:
            matches[file_path] = []
        matches[file_path].append(f"{line_num}:{content}")

    return matches

import difflib

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def compute_unified_diff(old_content: str, new_content: str, file_path: str):
    """Compute a unified diff between old and new content. Returns the diff string."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(old_lines, new_lines, fromfile=file_path, tofile=file_path)
    )
    if not diff_lines:
        logger.info("No diff for %s (content identical)", file_path)
        return ""

    diff_text = "".join(diff_lines)
    logger.info("Diff for %s: %d lines changed", file_path, len(diff_lines))
    return diff_text

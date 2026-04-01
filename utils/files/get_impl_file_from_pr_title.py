import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

BACKTICK_PATH_PATTERN = re.compile(r"`([^`]+)`")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_impl_file_from_pr_title(pr_title: str):
    if not pr_title:
        logger.warning("get_impl_file_from_pr_title: pr_title is empty")
        return None

    # Try backtick-wrapped path first (quality PR titles use this format)
    match = BACKTICK_PATH_PATTERN.search(pr_title)
    if match:
        candidate = match.group(1)
        if "/" in candidate or "." in candidate:
            return candidate

    # Fallback for old PRs created before backtick wrapping was added
    last_token = pr_title.split()[-1]
    if "/" in last_token or "." in last_token:
        return last_token

    logger.warning("No file path found in PR title: %s", pr_title)
    return None

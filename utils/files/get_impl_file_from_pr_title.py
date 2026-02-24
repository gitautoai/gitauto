from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_impl_file_from_pr_title(pr_title: str):
    if not pr_title:
        logger.warning("get_impl_file_from_pr_title: pr_title is empty")
        return None

    last_token = pr_title.split()[-1]
    if "/" in last_token or "." in last_token:
        return last_token

    logger.warning("No file path found in PR title: %s", pr_title)
    return None

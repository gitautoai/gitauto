from anthropic.types import ToolResultBlockParam

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

DIFF_MARKERS = [
    (
        "diff partially applied to the file: ",
        ". But, some changes were rejected",
        "diff_failure",
    ),
    (
        "diff applied to the file: ",
        " successfully by apply_diff_to_file",
        "diff_success",
    ),
]


@handle_exceptions(default_return_value=("", ""), raise_on_error=False)
def extract_diff_result_file_path(item: ToolResultBlockParam) -> tuple[str, str]:
    """Extract file path and action from a diff tool_result.

    Returns (filepath, action) where action is 'diff_failure' or 'diff_success'.
    Returns ('', '') if not a diff result.
    """
    item_content = item.get("content")
    if not isinstance(item_content, str):
        logger.info("extract_diff_result_file_path: content is not string, skipping")
        return ("", "")

    for marker, end, action in DIFF_MARKERS:
        s = item_content.find(marker)
        e = item_content.find(end)
        if s == -1 or e == -1:
            continue

        s += len(marker)
        if s >= e:
            logger.info("extract_diff_result_file_path: invalid marker positions")
            continue

        filepath = item_content[s:e]
        logger.info(
            "extract_diff_result_file_path: extracted %s (%s)", filepath, action
        )
        return (filepath, action)

    logger.info("extract_diff_result_file_path: no diff markers found")
    return ("", "")

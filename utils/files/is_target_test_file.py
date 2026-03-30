from pathlib import PurePosixPath

from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.get_impl_file_from_pr_title import get_impl_file_from_pr_title
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=True, raise_on_error=False)
def is_target_test_file(file_path: str, base_args: BaseArgs):
    if not is_test_file(file_path):
        logger.info("is_target_test_file: %s is not a test file", file_path)
        return False

    pr_title = base_args.get("pr_title", "")
    if not pr_title:
        logger.info("is_target_test_file: no pr_title, allowing edit for %s", file_path)
        return True

    implementation_file = get_impl_file_from_pr_title(pr_title)
    if not implementation_file:
        logger.info(
            "is_target_test_file: no file path in title, allowing edit for %s",
            file_path,
        )
        return True

    target_filename = PurePosixPath(implementation_file).stem
    is_target = target_filename.lower() in file_path.lower()
    logger.info(
        "is_target_test_file: %s, target=%s, file_path=%s",
        is_target,
        target_filename,
        file_path,
    )
    return is_target

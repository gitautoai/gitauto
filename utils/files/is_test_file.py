from constants.files import (
    TEST_DIR_PATTERNS,
    TEST_NAMING_PATTERNS,
    TEST_SUPPORT_PATTERNS,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_test_file(filename: str) -> bool:
    """Check if a file is a test file based on comprehensive patterns from constants.files."""
    if not isinstance(filename, str):
        logger.info("is_test_file: non-string input: %s", type(filename))
        return False

    filename_lower = filename.lower()

    for p in TEST_NAMING_PATTERNS:
        if p.detect.search(filename_lower):  # pylint: disable=no-member
            logger.info(
                "is_test_file: %s matched naming pattern %s",
                filename,
                p.detect.pattern,  # pylint: disable=no-member
            )
            return True

    for pattern in TEST_DIR_PATTERNS:
        if pattern.search(filename_lower):
            logger.info(
                "is_test_file: %s matched dir pattern %s", filename, pattern.pattern
            )
            return True

    for pattern in TEST_SUPPORT_PATTERNS:
        if pattern.search(filename_lower):
            logger.info(
                "is_test_file: %s matched support pattern %s", filename, pattern.pattern
            )
            return True

    logger.info("is_test_file: %s is not a test file", filename)
    return False

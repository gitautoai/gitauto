import os
import re

from utils.files.grep_files import grep_files
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Matches common test file naming conventions across languages
TEST_FILE_PATTERN = re.compile(
    r"(^test_|_test\.|\.test\.|\.spec\.|_spec\.|Test\.|Tests\.)", re.IGNORECASE
)


@handle_exceptions(default_return_value=[], raise_on_error=False)
def find_test_files(search_dir: str, impl_file_path: str):
    """Search the local clone for test files that reference the implementation file."""
    # "src/routes/middleware/audit-event.ts" -> "audit-event"
    stem = os.path.splitext(os.path.basename(impl_file_path))[0]
    if not stem:
        logger.warning("Could not extract stem from impl file path: %s", impl_file_path)
        return list[str]()

    file_paths = grep_files(query=stem, search_dir=search_dir)

    # Filter to test files and exclude the impl file itself
    test_files = [
        p
        for p in file_paths
        if TEST_FILE_PATTERN.search(os.path.basename(p)) and p != impl_file_path
    ]

    logger.info(
        "Found %d test files for %s (from %d grep hits): %s",
        len(test_files),
        impl_file_path,
        len(file_paths),
        test_files,
    )
    return test_files

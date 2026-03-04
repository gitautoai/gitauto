from pathlib import Path

from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger

# Common test subdirectory names that live next to source files
TEST_SUBDIRS = {
    "__tests__",  # Jest/Vitest convention
    "tests",  # Python, PHP, general
    "test",  # Java/Maven, Go
    "spec",  # RSpec (Ruby), Jasmine
    "e2e",  # End-to-end tests
    "cypress",  # Cypress E2E
    "playwright",  # Playwright E2E
    "testing",  # Python, general
    "__mocks__",  # Jest manual mocks
    "__snapshots__",  # Jest/Vitest snapshots
    "__fixtures__",  # Test fixtures
    "fixtures",  # Test fixtures (Django, Rails)
    "test-utils",  # Test utilities (kebab-case)
    "test_utils",  # Test utilities (snake_case)
    "test-helpers",  # Test helpers (kebab-case)
    "test_helper",  # Test helpers (snake_case, Rails)
    "stories",  # Storybook visual tests
}


@handle_exceptions(default_return_value=False, raise_on_error=False)
def has_test_file_candidate(item_path: str, all_file_paths: list[str]) -> bool:
    """Check if a test file exists for the given source file in a nearby directory.

    Requires directory proximity to avoid false positives where files with the
    same name in different directories are incorrectly matched. For example,
    src/utils/generateId.test.ts should NOT match
    src/models/graphql/operation/document/generateId.ts.
    """
    item_stem = Path(item_path).stem.lower()
    item_dir = str(Path(item_path).parent).lower()
    nearby_dirs = {item_dir} | {f"{item_dir}/{d}" for d in TEST_SUBDIRS}
    matched = next(
        (
            fp
            for fp in all_file_paths
            if is_test_file(fp)
            and item_stem in Path(fp).stem.lower()
            and str(Path(fp).parent).lower() in nearby_dirs
        ),
        None,
    )
    if matched:
        logger.info("Found nearby test file for %s: %s", item_path, matched)
    return matched is not None

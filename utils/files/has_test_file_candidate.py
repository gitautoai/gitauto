from pathlib import Path

from constants.files import TEST_DIR_NAMES
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def has_test_file_candidate(item_path: str, all_file_paths: list[str]) -> bool:
    """Check if a test file candidate exists for the given source file.

    Matches test files by stem name AND directory relationship:
    1. Same directory (colocated): src/utils/generateId.test.ts
    2. Child test subdirectory: src/models/__tests__/Quote.test.ts
    3. Mirror directory: test/spec/services/getPolicyInfo.test.ts for src/services/getPolicyInfo.ts

    Rejects false positives where files share a stem but are in unrelated directories.
    e.g. src/utils/generateId.test.ts should NOT match src/models/graphql/operation/document/generateId.ts.
    """
    item_stem = Path(item_path).stem.lower()
    item_dir = str(Path(item_path).parent).lower()
    child_test_dirs = {f"{item_dir}/{d}" for d in TEST_DIR_NAMES}
    for fp in all_file_paths:
        if not is_test_file(fp):
            continue
        if item_stem not in Path(fp).stem.lower():
            continue
        test_dir = str(Path(fp).parent).lower()
        # Same directory or child test subdirectory
        if test_dir == item_dir or test_dir in child_test_dirs:
            logger.info("Found test file candidate for %s: %s", item_path, fp)
            return True
        # Mirror directory: strip leading test dir components, match remaining subpath
        # e.g. test/spec/services/ -> strip test/, strip spec/ -> services/ matches src/services/
        test_parts = test_dir.split("/")
        stripped = 0
        while stripped < len(test_parts) and test_parts[stripped] in TEST_DIR_NAMES:
            stripped += 1
        if stripped > 0:
            mirror_subpath = "/".join(test_parts[stripped:])
            item_parts = item_dir.split("/")
            for i in range(len(item_parts)):
                if "/".join(item_parts[i:]) == mirror_subpath:
                    logger.info("Found test file candidate for %s: %s", item_path, fp)
                    return True
    return False

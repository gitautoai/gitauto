import os
from pathlib import PurePosixPath

from constants.files import SKIP_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.files.grep_files import grep_files
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def find_test_files(search_dir: str, impl_file_path: str):
    """Find test files for an implementation file.

    Stem is extracted from the filename (e.g. "src/routes/middleware/audit-event.ts" -> "audit-event",
    "src/pages/Quote/index.tsx" -> "index"). Test files found by union of path matching (path contains
    stem) and content grep (test files referencing the stem). Excludes the impl file itself.
    """
    stem = PurePosixPath(impl_file_path).stem
    if not stem:
        logger.warning("Could not extract stem from impl file path: %s", impl_file_path)
        return list[str]()

    # Path matching: walk file tree, find test files whose path contains the stem
    stem_lower = stem.lower()
    test_files: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(search_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not is_test_file(name):
                continue
            full_path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(full_path, search_dir)
            if rel_path != impl_file_path and stem_lower in rel_path.lower():
                test_files.add(rel_path)

    # Content grep: find additional test files that reference the stem in their content
    grep_hits = grep_files(query=stem, search_dir=search_dir)
    for p in grep_hits:
        if p != impl_file_path and is_test_file(os.path.basename(p)):
            test_files.add(p)

    logger.info("Found %d test files for %s", len(test_files), impl_file_path)
    return list(test_files)

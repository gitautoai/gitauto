from pathlib import PurePosixPath

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def prioritize_test_files(test_file_paths: list[str], impl_file_path: str):
    """Sort test file paths by relevance to the implementation file.

    Scoring:
    - Name match: +100 (test file name contains the impl file stem)
    - Same directory: +50
    - Shared common parent: +10 per shared path component
    - Distance penalty: -1 per path component difference
    """
    search_stem = PurePosixPath(impl_file_path).stem
    impl_dir = str(PurePosixPath(impl_file_path).parent)
    impl_parts = PurePosixPath(impl_file_path).parts

    scored: list[tuple[int, str]] = []
    for test_path in test_file_paths:
        score = 0
        test_parts = PurePosixPath(test_path).parts
        test_dir = str(PurePosixPath(test_path).parent)
        test_name = PurePosixPath(test_path).stem

        # Count shared leading path components (stop at first mismatch)
        common_len = 0
        for a, b in zip(impl_parts, test_parts):
            if a != b:
                break
            common_len += 1

        # Name match: test file name contains the meaningful search stem
        if search_stem and search_stem.lower() in test_name.lower():
            score += 100

        # Same directory
        if test_dir == impl_dir:
            score += 50
        # Share a common parent: more shared components = more relevant
        elif common_len > 0:
            score += common_len * 10

        # Distance penalty: number of unique path components between the two
        distance = (len(impl_parts) - common_len) + (len(test_parts) - common_len)
        score -= distance

        scored.append((score, test_path))

    scored.sort(key=lambda x: (-x[0], x[1]))
    result = [path for _, path in scored]
    logger.info(
        "prioritize_test_files: sorted %d test files for %s, top scores: %s",
        len(result),
        impl_file_path,
        list(scored[:3]),
    )
    return result

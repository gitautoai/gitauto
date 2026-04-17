import os

from constants.files import SKIP_DIRS, TOP_LEVEL_TEST_DIRS
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def detect_test_location_convention(clone_dir: str):
    counts: dict[str, int] = {"co-located": 0, "__tests__": 0, "separate": 0}
    examples: dict[str, str] = {}

    for dirpath, dirnames, filenames in os.walk(clone_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if not is_test_file(filename):
                continue

            rel_path = os.path.relpath(os.path.join(dirpath, filename), clone_dir)
            parts = rel_path.split(os.sep)

            if "__tests__" in parts:
                category = "__tests__"
            elif parts[0] in TOP_LEVEL_TEST_DIRS:
                category = "separate"
            else:
                category = "co-located"

            counts[category] += 1
            if category not in examples:
                examples[category] = rel_path

    logger.info(
        "Test location convention detection: counts=%s in %s", counts, clone_dir
    )

    total = sum(counts.values())
    if total == 0:
        logger.info("No test files found in %s, skipping location detection", clone_dir)
        return None

    dominant = max(counts, key=lambda k: counts[k])
    if counts[dominant] / total < 0.8:
        logger.info(
            "No dominant test location convention (best=%s at %d/%d) in %s",
            dominant,
            counts[dominant],
            total,
            clone_dir,
        )
        return None

    templates = {
        "co-located": "co-located (e.g., {example})",
        "__tests__": "__tests__ subdirectory (e.g., {example})",
        "separate": "separate test directory (e.g., {example})",
    }
    result = templates[dominant].format(example=examples[dominant])
    logger.info("Detected test location convention: %s", result)
    return result

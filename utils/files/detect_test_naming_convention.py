import os

from constants.files import SKIP_DIRS, TEST_NAMING_PATTERNS
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def detect_test_naming_convention(clone_dir: str):
    counts: dict[str, int] = {}
    examples: dict[str, str] = {}
    templates: dict[str, str] = {}

    # os.walk yields (dirpath, dirnames, filenames) for each directory in the tree:
    # e.g. ("/tmp/repo/src", ["models", "utils"], ["index.ts", "User.spec.ts"])
    for _dirpath, dirnames, filenames in os.walk(clone_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            filename_lower = filename.lower()
            for p in TEST_NAMING_PATTERNS:
                if p.detect.search(filename_lower):  # pylint: disable=no-member
                    counts[p.name] = counts.get(p.name, 0) + 1
                    if p.name not in examples:
                        examples[p.name] = filename
                        templates[p.name] = p.description
                    break  # One file matches at most one pattern

    logger.info("Test naming convention detection: counts=%s in %s", counts, clone_dir)

    if not counts:
        return None

    total = sum(counts.values())
    dominant = max(counts, key=lambda k: counts[k])

    # Require at least 60% dominance to declare a convention
    if counts[dominant] / total < 0.6:
        return None

    return templates[dominant].format(example=examples[dominant])

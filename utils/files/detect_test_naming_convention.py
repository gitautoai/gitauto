import os
import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SKIP_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "vendor",
        "coverage",
    }
)

# Each pattern maps to a human-readable description. Order matters: more specific first.
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("dot_spec", re.compile(r"\.spec\.\w+$"), "Use .spec. naming (e.g., {example})"),
    ("dot_test", re.compile(r"\.test\.\w+$"), "Use .test. naming (e.g., {example})"),
    (
        "test_prefix",
        re.compile(r"^test_.*\.py$"),
        "Use test_ prefix naming (e.g., {example})",
    ),
    (
        "Test_suffix",
        re.compile(r"[A-Z]\w*Test\.\w+$"),
        "Use Test suffix naming (e.g., {example})",
    ),
    (
        "underscore_test",
        re.compile(r"_test\.\w+$"),
        "Use _test suffix naming (e.g., {example})",
    ),
    (
        "underscore_spec",
        re.compile(r"_spec\.\w+$"),
        "Use _spec suffix naming (e.g., {example})",
    ),
]


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
            for convention, pattern, template in PATTERNS:
                if pattern.search(filename):
                    counts[convention] = counts.get(convention, 0) + 1
                    if convention not in examples:
                        examples[convention] = filename
                        templates[convention] = template
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

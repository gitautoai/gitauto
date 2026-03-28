import re

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
TEST_FILE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
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

# All test-related directory names (child subdirs, mirror prefixes, support dirs)
TEST_DIR_NAMES = {
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

# Top-level directories that indicate a "separate test directory" convention
TOP_LEVEL_TEST_DIRS = frozenset({"test", "tests", "spec", "specs", "t"})

JEST_CONFIG_FILES = [
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
]

VITEST_CONFIG_FILES = [
    "vitest.config.ts",
    "vitest.config.js",
    "vitest.config.mts",
    "vitest.config.mjs",
]

JS_TS_FILE_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")

PHP_TEST_FILE_EXTENSIONS = ("Test.php",)

TS_TEST_FILE_EXTENSIONS = (
    ".test.ts",
    ".test.tsx",
    ".spec.ts",
    ".spec.tsx",
)

JS_TEST_FILE_EXTENSIONS = (
    ".test.js",
    ".test.jsx",
    ".spec.js",
    ".spec.jsx",
) + TS_TEST_FILE_EXTENSIONS

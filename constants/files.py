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

# Test file naming patterns: (convention_name, regex, description_template)
# Used by is_test_file() for detection and detect_test_naming_convention() for classification.
# Order matters: more specific first.
TEST_NAMING_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("dot_spec", re.compile(r"\.spec\."), "Use .spec. naming (e.g., {example})"),
    ("dot_test", re.compile(r"\.test\."), "Use .test. naming (e.g., {example})"),
    (
        "test_prefix",
        re.compile(r"(^|/)test_"),
        "Use test_ prefix naming (e.g., {example})",
    ),
    (
        "underscore_test",
        re.compile(r"_test\."),
        "Use _test suffix naming (e.g., {example})",
    ),
    (
        "underscore_spec",
        re.compile(r"_spec\."),
        "Use _spec suffix naming (e.g., {example})",
    ),
    (
        "Test_suffix",
        re.compile(r"(?<!vi)tests?\."),
        "Use Test suffix naming (e.g., {example})",
    ),
    (
        "spec_prefix",
        re.compile(r"(^|/)spec_"),
        "Use spec_ prefix naming (e.g., {example})",
    ),
]

# Test directory patterns (path-based, not filename-based)
TEST_DIR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)e2e/"),
    re.compile(r"(^|/)cypress/"),
    re.compile(r"(^|/)playwright/"),
    re.compile(r"(^|/)spec/"),
    re.compile(r"(^|/)testing/"),
]

# Test support file patterns (mocks, fixtures, snapshots, helpers, storybook, CI)
TEST_SUPPORT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)__mocks__/"),
    re.compile(r"\.mock\."),
    re.compile(r"mocks?\."),
    re.compile(r"(^|/)__snapshots__/"),
    re.compile(r"\.snap$"),
    re.compile(r"(^|/)__fixtures__/"),
    re.compile(r"(^|/)fixtures/"),
    re.compile(r"\.fixture\."),
    re.compile(r"(^|/)test[-_]utils?/"),
    re.compile(r"(^|/)test[-_]helpers?/"),
    re.compile(r"(^|/)setuptests\."),
    re.compile(r"(^|/)testsetup\."),
    re.compile(r"(^|/)test[-_]setup\."),
    re.compile(r"\.stories\."),
    re.compile(r"(^|/)stories/"),
    re.compile(r"^test\."),
    re.compile(r"^spec\."),
    re.compile(r"^\.github/"),
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
